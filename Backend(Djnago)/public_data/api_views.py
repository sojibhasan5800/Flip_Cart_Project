import base64
import json
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import CursorPagination
from rest_framework import status
from django_redis import get_redis_connection
from admin_core.tasks import RedisOrgCounter
from flipcart_project import settings
from store.serializers import ProductListSerializer
from elasticsearch_dsl import Search

logger = logging.getLogger(__name__)


class GlobalLatestProductPagination(CursorPagination):
    page_size = 4
    cursor_query_param = "cursor"


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
                if len(products) < page_size:
                    products = self.get_from_elasticsearch(decoded_cursor)
                    source = "es"

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

        member_keys = redis_conn.zrevrange(global_key, 0, 49)

        products = []
        for member_key in member_keys:
            raw = redis_conn.hget(hash_key, member_key)
            if not raw:
                continue

            product = json.loads(raw)

            if cursor:
                if product["created_date"] > cursor["last_date"]:
                    continue
                if (
                    product["created_date"] == cursor["last_date"]
                    and member_key >= cursor["last_member"]
                ):
                    continue

            products.append(product)

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