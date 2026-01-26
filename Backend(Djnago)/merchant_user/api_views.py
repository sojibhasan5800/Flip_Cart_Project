
from httpcore import request
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from django.db.models import Q
from rest_framework.exceptions import ValidationError, PermissionDenied

from merchant_user.models import Organization, MerchantUser
from store.serializers import ProductCreateSerializer,ProductListSerializer
from .serializers import OrganizationCreateSerializer,BasicStoreInfoSerializer,ReviewSerializer
from rest_framework.permissions import IsAuthenticated
from .permissions import IsSuperAdmin,IsMerchantUser
from django_tenants.utils import schema_context
from django.db import connection, transaction
from django.db.models import Sum, Count
from datetime import timedelta
from store.models import Product,ReviewRating
from orders.models import Order, OrderProduct
from store.models import Product, ProductGallery
from store.serializers import ProductSerializer  



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

        serializer = OrganizationCreateSerializer(data=request.data)
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
                    "ratings": ReviewSerializer(recent_reviews, many=True).data
                }
            }

        return Response(data, status=status.HTTP_200_OK)
   


class MerchantProductAPIView(APIView):
    # permission_classes = [IsMerchantUser]


    def get(self, request):
        organization = getattr(request, "organization", None)
        if not organization:
            raise ValidationError("organization_id is required")
        

        
        products = (
            Product.objects
            .select_related("category")
            .order_by("-created_date")
        )

        # Basic pagination (real-world: use Pagination class from DRF)
        page = request.query_params.get('page', 1)
        page_size = request.query_params.get('page_size', 10)
        start = (int(page) - 1) * int(page_size)
        end = start + int(page_size)
        paginated_products = products[start:end]

        serializer = ProductListSerializer(paginated_products, many=True)
        return Response({
            "data": serializer.data,
            "count": products.count(),
            "page": int(page),
            "page_size": int(page_size)
        }, status=status.HTTP_200_OK)
        

    def post(self, request):
        organization = getattr(request, "organization", None)
        if not organization:
            raise ValidationError("organization_id is required")
        

        with transaction.atomic():
            # Serializer init
            serializer = ProductCreateSerializer(
                data=request.data,
                context={"organization": organization}
            )

            # Validate
            serializer.is_valid(raise_exception=True)

            # Save product
            serializer.save()

            #  You can do more DB operations here safely

        # 3️ Return response
        return Response(
            {
                "message": "Product added successfully",
                "data": serializer.data
            },
            status=status.HTTP_201_CREATED
        )

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