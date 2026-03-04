
import base64
import json
from django.conf import settings
from httpcore import request
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from django.db.models import Q
from rest_framework.exceptions import ValidationError, PermissionDenied
from redis.exceptions import ConnectionError as RedisConnectionError
from django_redis.exceptions import ConnectionInterrupted

from merchant_user.models import Organization, MerchantUser
from store.serializers import ProductCreateSerializer,ProductListSerializer
from .serializers import OrganizationCreateSerializer,BasicStoreInfoSerializer,ReviewSerializer
from rest_framework.permissions import IsAuthenticated
from .permissions import IsSuperAdmin,IsMerchantUser
from django_tenants.utils import schema_context
from django.db import connection, transaction
from django.db.models import Sum, Count
from datetime import timedelta
from elasticsearch_dsl import Search

from django_redis import get_redis_connection
from store.models import Product,ReviewRating
from orders.models import Order, OrderProduct
from store.models import Product, ProductGallery
from store.serializers import ProductSerializer  
import logging

logger = logging.getLogger(__name__)




class MerchantStoreCreateAPIView(APIView):
    """
    Merchant Store Create & Status API

    GET:
    - Check if merchant already submitted a store
    - Returns status: pending / approved / rejected

    POST:
    - Submit new store application
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        merchant_profile = MerchantUser.objects.filter(user=user).first()
        if not merchant_profile or not merchant_profile.organization:
            return Response(
                {"status": None},
                status=status.HTTP_200_OK
            )

        organization = merchant_profile.organization

        if organization.is_verified:
            store_status = "approved"
        elif organization.is_active:
            store_status = "pending"
        else:
            store_status = "rejected"

        return Response(
            {
                "status": store_status,
                "store_name": organization.business_name,
            },
            status=status.HTTP_200_OK
        )

    def post(self, request):
        user = request.user
        data = request.data
        username = data.get("username")
        business_email = data.get("business_email")

    # 🔹 Single query to check duplicates
        duplicate_store = Organization.objects.filter(
            Q(username=username) | Q(business_email=business_email)
        ).first()

        if duplicate_store:
            if duplicate_store.username == username:
                return Response(
                    {"error": f"Username '{username}' is already taken."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if duplicate_store.business_email == business_email:
                return Response(
                    {"error": f"Email '{business_email}' is already used for another store."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        serializer = OrganizationCreateSerializer(data=request.data, context={"user": user})
        serializer.is_valid(raise_exception=True)

        with schema_context("public"), transaction.atomic():
            organization = serializer.save()

            MerchantUser.objects.create(
                user=user,
                organization=organization,
                role="owner",
                is_active=True,
                is_verified=False,
            )

        return Response(
            {
                "message": "Store application submitted successfully.",
                "status": "pending",
                "store_url": organization.store_url
            },
            status=status.HTTP_201_CREATED
        )

    

class SellerStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Find all active merchant profiles of the user
        profiles = MerchantUser.objects.filter(
            user=user,
            is_active=True,
        ).select_related('organization').order_by('organization__business_name')

        if not profiles.exists():
            return Response({
                "is_seller": False,
                "status": "no_store",
                "message": "No store found",
                "possible_stores": []
            }, status=status.HTTP_200_OK)

        # If only one store exists → directly check approval and return data
        if profiles.count() == 1:
            profile = profiles.first()
            org = profile.organization

            if org.is_verified and org.is_active:
                possible_stores = []
                # serializer = BasicStoreInfoSerializer(org)
                
                # return Response({
                #     "is_seller": True,
                #     "status": "approved",
                #     "role": profile.role,
                #     "store": {
                #         **serializer.data,
                #         "store_url": org.store_url,
                #         "org_id": org.id,
                #     }
                # })
                possible_stores.append({
                "org_id": org.id,
                "business_email": org.business_email,
                "business_name": org.business_name,
                "store_logo": org.store_logo,
                "store_url": org.store_url,
                "status": (
                        "approved" if (org.is_active and org.is_verified)
                        else "pending" if org.is_active
                        else "rejected"
                        )
                })
                print(possible_stores)
                return Response({
                    "is_seller": True,
                    "status": "approved",
                    "role": profile.role,
                    "message": "One stores found.",
                    "possible_stores": possible_stores
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "is_seller": False,
                    "status": "pending" if org.is_active else "rejected",
                    "message": "Store has not been approved yet",
                    "possible_stores": [{
                        "org_id": org.id,
                        "business_email": org.business_email,
                        "business_name": org.business_name,
                        "status": "pending" if org.is_active else "rejected"
                    }]
                })

        # If multiple stores exist → return list only (frontend will ask user to select)
        possible_stores = []
        for profile in profiles:
            org = profile.organization
            possible_stores.append({
                "org_id": org.id,
                "business_email": org.business_email,
                "business_name": org.business_name,
                "store_logo": org.store_logo,
                "store_url": org.store_url,
                "status": (
                        "approved" if (org.is_active and org.is_verified)
                        else "pending" if org.is_active
                        else "rejected"
                        )
            })

        return Response({
            "is_seller": False,
            "status": "multiple_stores",
            "message": "Multiple stores found. Please select one.",
            "possible_stores": possible_stores
        }, status=status.HTTP_200_OK)

    def post(self, request):
        user = request.user
        business_email = request.data.get("business_email")

        if not business_email:
            return Response({"error": "business_email is required"}, status=400)

        try:
            profile = MerchantUser.objects.get(
                user=user,
                is_active=True,
                organization__business_email=business_email
            )
        except MerchantUser.DoesNotExist:
            return Response({"error": "No store found with this email"}, status=404)

        org = profile.organization

        if not (org.is_verified and org.is_active):
            return Response({
                "is_seller": False,
                "status": "not_approved",
                "message": "This store is not approved"
            }, status=403)

        serializer = BasicStoreInfoSerializer(org)

        return Response({
            "is_seller": True,
            "status": "approved",
            "role": profile.role,
            "store": {
                **serializer.data,
                "store_url": org.store_url,
            }
        }, status=200)



class SellerStoreDashboardAPIView(APIView):
    """
    Merchant/Seller Dashboard - Tenant specific data only
    Endpoint: GET /api/merchant_user/seller-store-dashboard/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # 1. Check if user is a merchant/staff of any organization
        merchant_profile = MerchantUser.objects.filter(user=user).select_related('organization').first()
        if not merchant_profile:
            return Response(
                {"error": "You are not associated with any store."},
                status=status.HTTP_403_FORBIDDEN
            )

        organization = merchant_profile.organization
        trial_ends_at = organization.trial_ends_at
        is_trail = organization.is_trial
        has_active_subscription = organization.has_active_subscription
        subscription_current_period_start = organization.subscription_current_period_start
        subscription_current_period_end = organization.subscription_current_period_end
        subscription_plan_level = organization.subscription_plan_level


        # 2. Switch to tenant schema
        with schema_context(organization.schema_name):
            # ────────────────────────────────────────────────
            # Total Products
            # ────────────────────────────────────────────────
            total_products = Product.objects.filter(is_available=True).count()

            # ────────────────────────────────────────────────
            # Total Earnings (completed + paid orders)
            # ────────────────────────────────────────────────
            earnings = OrderProduct.objects.filter(
                order__is_ordered=True,
                order__status__in=['Completed', 'Delivered']
            ).aggregate(
                total=Sum('product_price') * Sum('quantity')
            ).get('total') or 0

            # ────────────────────────────────────────────────
            # Total Orders
            # ────────────────────────────────────────────────
            total_orders = Order.objects.filter(
                is_ordered=True
            ).count()

            # ────────────────────────────────────────────────
            # Recent Reviews (last 30 days, limit 10)
            # ────────────────────────────────────────────────
            thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
            recent_reviews = ReviewRating.objects.filter(
                created_at__gte=thirty_days_ago,
                status=True
            ).select_related(
                'user', 'product', 'product__category'
            ).order_by('-created_at')[:10]

            # 3. Prepare response data
            data = {
                "dashboardData": {
                    "totalProducts": total_products,
                    "totalEarnings": float(earnings),  # decimal → float for JSON
                    "totalOrders": total_orders,
                    "ratings": ReviewSerializer(recent_reviews, many=True).data,
                    "subscription": {
                        "is_trial": is_trail,
                        "trial_ends_at": trial_ends_at,
                        "has_active_subscription": has_active_subscription,
                        "current_period_start": subscription_current_period_start,
                        "current_period_end": subscription_current_period_end,
                        "plan_name": subscription_plan_level,
                    }
                }
            }
            print("Dashboard data prepared:", data)

        return Response(data, status=status.HTTP_200_OK)

class MerchantProductAPIView(APIView):
    page_size = 10  # Default page size

    def get(self, request):

        organization = getattr(request, "organization", None)
        if not organization:
            raise ValidationError("organization_id is required")

        products = []
        source = "none"
        next_cursor = None

        # Redis connection try block
        try:
            redis = get_redis_connection("default")
            org_key = f"tenant:{organization.id}:latest_products"
            hash_key = f"tenant:{organization.id}:product:data"

            # Cursor decode
            cursor = request.query_params.get("cursor")
            last_ts = None
            last_id = None

            if cursor:
                try:
                    decoded = json.loads(base64.b64decode(cursor).decode())
                    last_ts = decoded.get("last_ts")
                    last_id = decoded.get("last_id")
                    source = decoded.get("source", "redis")
                except Exception:
                    return Response({"error": "Invalid cursor"}, status=400)

            # STEP 1: Redis fetch (primary & fast path)
            raw_ids = redis.zrevrange(org_key, 0, 999)  # max 1000 latest

            for pid in raw_ids:
                raw = redis.hget(hash_key, pid)
                if not raw:
                    continue

                try:
                    item = json.loads(raw.decode())
                except json.JSONDecodeError:
                    continue

                if not item.get("is_available", True):
                    continue

                # Cursor filtering
                if last_ts:
                    if item["created_date"] > last_ts:
                        continue
                    if item["created_date"] == last_ts and item["id"] >= last_id:
                        continue

                products.append(item)
                if len(products) >= self.page_size:
                    break

            source = "redis"

        except (RedisConnectionError, ConnectionInterrupted, Exception) as redis_err:
            # Redis fail/down → empty data return (no ES fallback)
            logger.warning(f"Redis unavailable for org {organization.id}: {redis_err}")
            products = []  # খালি ডাটা
            source = "none"

        # STEP 2: ES fallback শুধু Redis successful + ডাটা কম হলে
        # তোমার নতুন রুল: Redis fail হলে ES ব্যবহার করবে না
        if len(products) < self.page_size and source == "redis":  # Redis success + data কম
            if not getattr(settings, 'ELASTICSEARCH_OFFLINE', True):
                try:
                    s = Search(using="default", index="products").filter(
                        "term", is_available=True
                    ).filter(
                        "term", organization_id=organization.id
                    )

                    if last_ts:
                        s = s.query(
                            "bool",
                            should=[
                                {"range": {"created_date": {"lt": last_ts}}},
                                {
                                    "bool": {
                                        "must": [
                                            {"term": {"created_date": last_ts}},
                                            {"range": {"id": {"lt": last_id}}},
                                        ]
                                    }
                                },
                            ],
                            minimum_should_match=1,
                        )

                    s = s.sort("-created_date", "-id")[:self.page_size - len(products)]
                    response = s.execute()

                    es_products = [hit.to_dict() for hit in response]
                    products.extend(es_products)

                    source = "es" if es_products else "redis"

                except Exception as es_err:
                    logger.error(f"ES fallback failed for org {organization.id}: {es_err}")
                    # ES fail হলেও Redis-এর ডাটা দিয়ে চলবে (no crash)

        # Next cursor
        if products:
            last_item = products[-1]
            cursor_data = {
                "source": source,
                "last_ts": last_item["created_date"],
                "last_id": last_item["id"],
            }
            next_cursor = base64.b64encode(json.dumps(cursor_data).encode()).decode()

        return Response({
            "data": products,          # Redis down → []
            "next_cursor": next_cursor,
            "source": source,          # frontend debug-এর জন্য
        }, status=200)

    def post(self, request):
        organization = getattr(request, "organization", None)
        if not organization:
            raise ValidationError("organization_id is required")
        
        with transaction.atomic():
            serializer = ProductCreateSerializer(
                data=request.data,
                context={"organization": organization}
            )
            serializer.is_valid(raise_exception=True)
            product = serializer.save()

        return Response({
            "message": "Product added successfully",
            "data": serializer.data
        }, status=201)
    
class ToggleStockAPIView(APIView):
    def patch(self, request, pk):
        try:
            organization = getattr(request, "organization", None)
            print("Organization found:", organization)
            if not organization:
                return Response({"error": "Organization not found"}, status=400)

            product = get_object_or_404(Product, pk=pk, organization=organization)

            old_status = product.is_available
            if product.stock == 0:
                product.is_available = False
            else:
                product.is_available = not old_status

            product.save(update_fields=['is_available'])

            return Response({
                "is_available": product.is_available,
                "previous_status": old_status,
                "message": "Stock toggled successfully"
            })

        except Exception as e:
            # সব ধরনের unexpected error catch
            print(f"ToggleStock error: {str(e)}")
            return Response({
                "error": "Server error occurred. Please try again later."
            }, status=500)