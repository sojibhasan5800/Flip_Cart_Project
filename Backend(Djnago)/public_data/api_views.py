import base64
import json
import logging
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import CursorPagination
from rest_framework import status
from django_redis import get_redis_connection
from admin_core.tasks import RedisOrgCounter
from django_tenants.utils import schema_context
from django_redis import get_redis_connection
from django.db.models import Count, Prefetch, Q
from flipcart_project import settings
from store.serializers import ProductListSerializer
from elasticsearch_dsl import Search
from store.models import Product, Variation, ProductGallery
from store.serializers import ProductDetailSerializer
from store.utils import get_reviews_page

logger = logging.getLogger(__name__)


class GlobalLatestProductPagination(CursorPagination):
    page_size = 12
    page_size_query_param = 'page_size'   # frontend থেকে ?page_size=20 পাঠালে কাজ করবে
    max_page_size = 40
    cursor_query_param = "cursor"

class LatestProductsAPIView(APIView):
    """
    Return latest 4 products globally or per tenant
    """

    def get(self, request):
        # Determine tenant schema
       
        redis_client = get_redis_connection("default")

        # Fetch latest 4 products from Redis global cache
        latest_keys = redis_client.zrange("global:latest_products", 0, 3)  # top 4
        product_hash = "global:product:data"
        products = []

        for key in latest_keys:
            raw = redis_client.hget(product_hash, key)
            if raw:
                product = json.loads(raw)
                products.append(product)

        return Response(products)


class HomeProductsAPIView(APIView):
    pagination_class = GlobalLatestProductPagination

    def get(self, request):
        try:
            # --------------------------------------------------
            # 1️ Decode cursor
            # --------------------------------------------------
            cursor = request.query_params.get("cursor")
            decoded_cursor = None

            if cursor:
                decoded_cursor = json.loads(
                    base64.b64decode(cursor).decode()
                )

            # --------------------------------------------------
            # 2️ Organization count (Redis first)
            # --------------------------------------------------
            redis_conn = get_redis_connection("default")
            org_count_key = "active_verified_org_count"
            org_count = redis_conn.get(org_count_key)

            if org_count is None:
                org_count = RedisOrgCounter().get_count()
            else:
                org_count = int(org_count)

            # --------------------------------------------------
            # 3️ Decide data source (CORE LOGIC)
            # --------------------------------------------------
            source = "redis"
            page_size = self.pagination_class.page_size

            #  RULE 1: Large scale → ES ONLY
            if org_count > 100:
                pass  # ES-only mode

                # if not getattr(settings, "ELASTICSEARCH_OFFLINE", False):
                #     products = self.get_from_elasticsearch(decoded_cursor)
                #     source = "es"
                # else:
                #     products = []  # Local এ ES নেই

            else:
                #  Small scale → Redis first
                products = self.get_from_redis(redis_conn, decoded_cursor)

                #  Redis exhausted → fallback to ES
                # if len(products) < page_size:
                #     products = self.get_from_elasticsearch(decoded_cursor)
                #     source = "es"

            # --------------------------------------------------
            # 4️ Pagination slice
            # --------------------------------------------------
            page_products = products[:page_size]

            next_cursor = None
            if page_products:
                last_item = page_products[-1]
                next_cursor = self.generate_cursor(last_item, source)

            # serializer = ProductListSerializer(page_products, many=True)

            return Response(
                {
                    "results": page_products,
                    "next_cursor": next_cursor,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"HomeProductsAPIView error: {e}", exc_info=True)
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # ======================================================
    # 🔹 Redis global feed (latest 5000)
    # ======================================================
    def get_from_redis(self, redis_conn, cursor):
        global_key = "global:latest_products"
        hash_key = "global:product:data"

        # Decode Redis ZSET members from bytes to string
        member_keys = redis_conn.zrange(global_key, 0, 49)
        member_keys = [key.decode('utf-8') if isinstance(key, bytes) else key for key in member_keys]

        products = []
        skip_until_passed = False

        if cursor:
            last_date = cursor["last_date"]
            last_member = cursor["last_member"]

            for member_key in member_keys:
                raw = redis_conn.hget(hash_key, member_key)
                if not raw:
                    continue

                product = json.loads(raw)

                # First, skip all products that are newer than last_date
                if product["created_date"] > last_date:
                    continue

                # If created_date is equal, skip products up to last_member
                if product["created_date"] == last_date:
                    if member_key <= last_member:  # ← use <= for correct string comparison
                        continue
                    else:
                        skip_until_passed = True

                # Add product only after skip condition is passed
                if skip_until_passed or product["created_date"] < last_date:
                    products.append(product)

                # Optional: stop early if more than required items are collected
                if len(products) >= self.pagination_class.page_size * 2:
                    break

        else:
            # If no cursor is provided, return the first page
            for member_key in member_keys:
                raw = redis_conn.hget(hash_key, member_key)
                if raw:
                    products.append(json.loads(raw))

        return products
    # ======================================================
    # 🔹 Elasticsearch (all older products)
    # # ======================================================
    # def get_from_elasticsearch(self, cursor):
    #     s = Search(using="default", index="products_feed").filter(
    #         "term", is_available=True
    #     )

    #     if cursor:
    #         s = s.query(
    #             "bool",
    #             should=[
    #                 {"range": {"created_date": {"lt": cursor["last_date"]}}},
    #                 {
    #                     "bool": {
    #                         "must": [
    #                             {"term": {"created_date": cursor["last_date"]}},
    #                             {"range": {"id": {"lt": cursor.get("last_id", 0)}}},
    #                         ]
    #                     }
    #                 },
    #             ],
    #             minimum_should_match=1,
    #         )

    #     s = s.sort("-created_date", "-id")[:10]
    #     response = s.execute()

    #     return [hit.to_dict() for hit in response]

    # ======================================================
    # 🔹 Cursor generator
    # ======================================================
    def generate_cursor(self, last_org_product, source):
        data = {
            "source": source,  # redis | es
            "last_date": last_org_product["created_date"],
            "last_member": f"{last_org_product['organization_id']}:{last_org_product['id']}",
            "last_id": last_org_product["id"],
        }
        return base64.b64encode(json.dumps(data).encode()).decode()

class ProductDetailView(APIView):
    """
    SaaS-aware Product Detail View (SAFE & OPTIMIZED)
    """

    def get(self, request, product_id):

        # 1️⃣ Detect tenant safely
        if not hasattr(request, "tenant"):
            return Response(
                {"detail": "Tenant not found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        tenant = request.tenant
        schema_name = tenant.schema_name
        redis_client = get_redis_connection("default")

        # 2️⃣ Check store status
        if not tenant.is_active:
            return Response(
                {"detail": "Store is inactive"},
                status=status.HTTP_403_FORBIDDEN
            )

        with schema_context(schema_name):

            # 3️⃣ Fetch product (tenant-safe)
            product = get_object_or_404(
                Product.objects.select_related(
                    'category', 'organization'
                ).prefetch_related(
                    Prefetch(
                        'variation_set',
                        queryset=Variation.objects.filter(is_active=True)
                    ),
                    Prefetch(
                        'productgallery_set',
                        queryset=ProductGallery.objects.only('id', 'images')
                    )
                ).annotate(
                    gallery_count=Count('productgallery', distinct=True),
                    review_count=Count(
                        'reviewrating',
                        distinct=True,
                        filter=Q(reviewrating__status=True)
                    )
                ),
                id=product_id,
                organization=tenant   # 🔒 IMPORTANT: tenant isolation
            )

            # 4️⃣ Redis cache (tenant-aware)
            cache_key = f"{schema_name}:product:{product.id}:latest_reviews:v1"
            latest_reviews = []

            cached = redis_client.get(cache_key)
            if cached:
                latest_reviews = json.loads(cached)
            else:
                reviews_qs = (
                    product.reviewrating_set
                    .filter(status=True)
                    .select_related('user')
                    .order_by('-created_at')[:5]
                )

                for r in reviews_qs:
                    latest_reviews.append({
                        "full_name": (
                            f"{getattr(r.user, 'first_name', '')} "
                            f"{getattr(r.user, 'last_name', '')}"
                        ).strip() or "Anonymous",
                        "rating": r.rating,
                        "subject": r.subject,
                        "review": r.review,
                        "updated_at": r.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                    })

                redis_client.set(
                    cache_key,
                    json.dumps(latest_reviews),
                    ex=300  # 5 minutes
                )

            # 5️⃣ Serialize response
            serializer = ProductDetailSerializer(
                product,
                context={"reviews": latest_reviews}
            )

            return Response(serializer.data, status=status.HTTP_200_OK)
        

class ProductReviewsView(APIView):
    """
    SaaS-aware, cursor-based paginated reviews
    """
    def get(self, request, product_id):
        limit = int(request.GET.get("limit", 20))
        cursor = request.GET.get("cursor")
        cursor = float(cursor) if cursor else None

        schema_name = request.tenant.schema_name if hasattr(request, "tenant") else "public"

        with schema_context(schema_name):
            # Redis key includes tenant
            redis_key = f"{schema_name}:product:{product_id}:reviews"
            reviews, next_cursor = get_reviews_page(product_id, limit=limit, cursor=cursor, redis_key=redis_key)

        return Response({
            "results": reviews,
            "next_cursor": next_cursor,
            "has_more": bool(next_cursor)
        })

