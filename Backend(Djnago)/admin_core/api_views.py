# views.py
from urllib import response
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.db import transaction, connection
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django_tenants.utils import get_tenant_model, schema_context

from orders.models import Order
from merchant_user.models import Organization, MerchantUser
from .models import Coupon
from .serializers import CouponSerializer, OrganizationApprovalSerializer
from .permissions import IsTenantAdmin, IsSuperAdmin
from .filters import CouponFilter
from .tasks import RedisOrgCounter

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django_celery_beat.models import PeriodicTask

import logging

logger = logging.getLogger(__name__)


class PublicAdminCheckAPIView(APIView):
    """
    Simple endpoint to check if current user is public schema admin
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Check if user is public admin",
        tags=["Auth / Debug"],
        responses={200: openapi.Response("Admin check result")}
    )
    def get(self, request):
        return Response({
            "is_public_admin": getattr(request, "is_public_admin", False),
            "user": request.user.email
        })


class PublicSchemaAPIView(APIView):
    """
    Base view that always runs inside public schema context
    """

    def dispatch(self, request, *args, **kwargs):
        with schema_context("public"):
            return super().dispatch(request, *args, **kwargs)


class SuperAdminDashboardAPIView(APIView):
    """
    Super Admin Platform-wide Dashboard
    Only accessible in PUBLIC schema
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Super Admin Platform Dashboard",
        operation_description="Shows very basic aggregated stats across all tenants",
        tags=["Dashboard / Super Admin"],
        responses={200: openapi.Response("Platform overview stats")}
    )
    def get(self, request):
        user = request.user

        if not user.is_superadmin:
            return Response({"detail": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

        TenantModel = get_tenant_model()
        tenants = TenantModel.objects.exclude(schema_name="public")

        total_orders = 0
        total_stores = 0

        # Note: commented aggregation – usually very slow without proper indexing / caching
        # for tenant in tenants:
        #     with schema_context(tenant.schema_name):
        #         total_orders += Order.objects.filter(is_ordered=True).count()
        #         total_stores += Organization.objects.filter(is_active=True).count()

        print(total_orders, total_stores)  # for debugging

        return Response({
            "role": "super_admin",
            "cards": {
                "products": 0,          # placeholder – can be extended later
                "revenue": 0,           # placeholder
                "orders": total_orders,
                "stores": total_stores,
            },
            "allOrders": [],           # MUST exist (frontend expectation)
        }, status=status.HTTP_200_OK)


class AdminStoreApprovalAPIView(PublicSchemaAPIView):
    """
    Super Admin – Manage store approval (public schema only)

    GET:
        ?status=pending     → List pending stores
        ?status=approved    → List approved/live stores

    POST /approve/      → Approve a store
    PUT  /reject/       → Reject & delete store (public row only)
    PATCH /toggle-active/ → Toggle verification status
    """
    permission_classes = [IsSuperAdmin]
    # RedisOrgCounter instance
    org_counter = RedisOrgCounter()

    @swagger_auto_schema(
        operation_summary="List pending or approved stores",
        manual_parameters=[
            openapi.Parameter('status', openapi.IN_QUERY,
                              description="pending or approved", type=openapi.TYPE_STRING)
        ],
        tags=["Store Management / Super Admin"]
    )
    def drop_tenant_schema(self, schema_name):
        """
        Safely drop a PostgreSQL tenant schema
        """
        if not schema_name:
            return

        protected_schemas = ["public", "public_user"]
        if schema_name in protected_schemas:
            raise Exception("Protected schema cannot be deleted")

        with connection.cursor() as cursor:
            cursor.execute(
                f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE;'
            )
    
    def get(self, request):
        status_param = request.query_params.get("status")

        if status_param == "pending":
            stores = Organization.objects.filter(
                is_verified=False,
                is_active=True
            )
        elif status_param == "approved":
            stores = Organization.objects.filter(
                is_verified=True,
                is_active=True
            )
        else:
            return Response(
                {"error": "Invalid status. Use 'pending' or 'approved'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = OrganizationApprovalSerializer(
            stores.order_by("-created_at"),
            many=True
        )

        return Response({
            "count": stores.count(),
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Approve a store",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'storeId': openapi.Schema(type=openapi.TYPE_INTEGER)
            },
            required=['storeId']
        ),
        tags=["Store Management / Super Admin"]
    )
    def post(self, request):
        org_id = request.data.get("storeId")

        if not org_id:
            return Response({"error": "storeId is required"}, status=400)

        organization = get_object_or_404(Organization, id=org_id)

        if organization.is_verified:
            return Response({"error": "Store is already approved"}, status=400)

        organization.is_verified = True
        organization.is_active = True
        organization.is_trial = True
        organization.onboarded_at = timezone.now()
        organization.save()
        #  Redis increment
        self.org_counter.increment()

        return Response({
            "message": "Store approved successfully",
            "store_name": organization.business_name
        }, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Reject and delete store (public schema only)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'storeId': openapi.Schema(type=openapi.TYPE_INTEGER)
            },
            required=['storeId']
        ),
        tags=["Store Management / Super Admin"]
    )
    def put(self, request):
        org_id = request.data.get("storeId")

        if not org_id:
            return Response({"error": "storeId is required"}, status=400)

        try:
            org_id = int(org_id)
        except ValueError:
            return Response({"error": "Invalid storeId format"}, status=400)

        organization = get_object_or_404(Organization, id=org_id)

        if organization.is_verified:
            return Response(
                {"error": "Approved store cannot be rejected"},
                status=400
            )

        schema_name = organization.schema_name
        # TenantModel = get_tenant_model()
        try:
            with transaction.atomic():

                # 1️⃣ Delete merchant users (public schema)
                merchant_users = MerchantUser.objects.filter(
                    organization=organization
                )
                deleted_users = list(
                    merchant_users.values_list("user__email", flat=True)
                )
                deleted_count = merchant_users.count()
                merchant_users.delete()

                # 2️⃣ Delete domains
                print(organization.domains.all())
                organization.domains.all().delete()


                # 3️⃣ DROP tenant schema (CRITICAL PART)
                self.drop_tenant_schema(schema_name)
                
                # 4️⃣ Delete organization row (public)
                # 4. Delete Organization row with RAW SQL (bypass ORM collector)
                with connection.cursor() as cursor:
                    cursor.execute("""
                        DELETE FROM merchant_user_organization 
                        WHERE id = %s
                    """, [organization.id])
                #  Redis decrement
                self.org_counter.decrement()


            return Response({
                "message": "Store rejected and tenant schema deleted successfully",
                "deleted_schema": schema_name,
                "deleted_merchant_users_count": deleted_count,
                "deleted_users_emails": deleted_users
            }, status=200)

        except Exception as e:
            logger.error(
                f"Store rejection failed for org_id={org_id}",
                exc_info=True
            )
            return Response({
                "error": "Store rejection failed",
                "detail": str(e)
            }, status=500)

    @swagger_auto_schema(
        operation_summary="Toggle store verification status",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'storeId': openapi.Schema(type=openapi.TYPE_INTEGER)
            },
            required=['storeId']
        ),
        tags=["Store Management / Super Admin"]
    )
    def patch(self, request):
        try:
            org_id = int(request.data.get("storeId"))
        except (TypeError, ValueError):
            return Response({"error": "Valid storeId is required"}, status=400)

        try:
            organization = Organization.objects.get(
                id=org_id,
                is_verified=True
            )
        except Organization.DoesNotExist:
            return Response({"error": "Store not found or not approved"}, status=404)

        # Toggle verification
        organization.is_verified = not organization.is_verified
        organization.save(update_fields=["is_verified"])

        return Response({
            "message": "Store status updated successfully",
            "is_active": organization.is_active,
            "is_verified": organization.is_verified,
            "id": organization.id
        }, status=status.HTTP_200_OK)


# ────────────────────────────────────────────────
# Coupon List + Create
# ────────────────────────────────────────────────
class CouponListCreateAPIView(APIView):
    """
    List all coupons + Create new coupon
    """
    permission_classes = [IsAuthenticated, IsTenantAdmin]

    @swagger_auto_schema(
        operation_summary="List coupons (with filters)",
        manual_parameters=[
            openapi.Parameter('status', openapi.IN_QUERY,
                              enum=['active', 'expired', 'upcoming', 'inactive'],
                              description="Filter by coupon status", type=openapi.TYPE_STRING),
        ],
        tags=["Coupons"]
    )
    def get(self, request):
        user = request.user
        now = timezone.now()

        if user.is_superadmin:
            queryset = Coupon.objects.all()
        else:
            if not user.organization:
                return Response({"error": "You are not associated with any store"}, status=400)
            queryset = Coupon.objects.filter(organization=user.organization)

        # Status filtering
        status_param = request.query_params.get('status')
        if status_param:
            if status_param == 'active':
                queryset = queryset.filter(is_active=True, valid_to__gt=now, valid_from__lte=now)
            elif status_param == 'expired':
                queryset = queryset.filter(Q(valid_to__lte=now) | Q(is_expired=True))
            elif status_param == 'upcoming':
                queryset = queryset.filter(is_active=True, valid_from__gt=now)
            elif status_param == 'inactive':
                queryset = queryset.filter(is_active=False)

        # Apply other filters, search, ordering via CouponFilter
        queryset = CouponFilter(request.query_params, queryset=queryset, request=request).qs

        serializer = CouponSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Create a new coupon",
        request_body=CouponSerializer,
        tags=["Coupons"]
    )
    def post(self, request):
        serializer = CouponSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            coupon = serializer.save()
            logger.info(f"Coupon created: {coupon.code} by {request.user.email}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ────────────────────────────────────────────────
# Single Coupon – Detail / Update / Delete
# ────────────────────────────────────────────────
class CouponDetailAPIView(APIView):
    """
    Retrieve / Update / Delete a single coupon by code
    """
    permission_classes = [IsAuthenticated, IsTenantAdmin]

    def get_object(self, request, code):
        code = code.upper()
        user = request.user
        try:
            if user.is_superadmin:
                return Coupon.objects.get(code=code)
            else:
                return Coupon.objects.get(code=code, organization=user.organization)
        except Coupon.DoesNotExist:
            return None

    @swagger_auto_schema(operation_summary="Get coupon detail", tags=["Coupons"])
    def get(self, request, code):
        coupon = self.get_object(request, code)
        if not coupon:
            return Response({"error": "Coupon not found"}, status=404)
        serializer = CouponSerializer(coupon)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Update coupon (partial allowed)",
        request_body=CouponSerializer(partial=True),
        tags=["Coupons"]
    )
    def put(self, request, code):
        coupon = self.get_object(request, code)
        if not coupon:
            return Response({"error": "Coupon not found"}, status=404)

        serializer = CouponSerializer(coupon, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            logger.info(f"Coupon updated: {coupon.code}")
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    @swagger_auto_schema(operation_summary="Delete coupon", tags=["Coupons"])
    def delete(self, request, code):
        coupon = self.get_object(request, code)
        if not coupon:
            return Response({"error": "Coupon not found"}, status=404)

        coupon.cancel_scheduled_task()
        coupon.delete()
        logger.warning(f"Coupon deleted: {code} by {request.user.email}")
        return Response({"message": "Coupon deleted successfully"}, status=204)


# ────────────────────────────────────────────────
# Coupon Activate / Deactivate
# ────────────────────────────────────────────────
class CouponToggleAPIView(APIView):
    """
    Activate or deactivate a coupon
    """
    permission_classes = [IsAuthenticated, IsTenantAdmin]

    @swagger_auto_schema(
        operation_summary="Activate or deactivate coupon",
        manual_parameters=[
            openapi.Parameter('code', openapi.IN_PATH, type=openapi.TYPE_STRING),
            openapi.Parameter('action', openapi.IN_PATH, enum=['activate', 'deactivate'], type=openapi.TYPE_STRING),
        ],
        tags=["Coupons"]
    )
    def post(self, request, code, action):
        if action not in ['activate', 'deactivate']:
            return Response({"error": "Invalid action. Use 'activate' or 'deactivate'"}, status=400)

        coupon = Coupon.objects.filter(code=code.upper()).first()
        if not coupon:
            return Response({"error": "Coupon not found"}, status=404)

        if not request.user.is_superadmin and coupon.organization != request.user.organization:
            return Response({"error": "This coupon does not belong to your store"}, status=403)

        if action == 'activate':
            if coupon.is_active:
                return Response({"message": "Coupon is already active"}, status=400)
            if coupon.valid_to <= timezone.now():
                return Response({"message": "Cannot activate an expired coupon"}, status=400)
            coupon.is_active = True
            coupon.schedule_expiry_task()
        else:
            if not coupon.is_active:
                return Response({"message": "Coupon is already inactive"}, status=400)
            coupon.is_active = False
            coupon.cancel_scheduled_task()

        coupon.save(update_fields=['is_active', 'updated_at'])

        status_msg = "activated" if action == 'activate' else "deactivated"
        return Response({
            "message": f"Coupon '{coupon.code}' has been {status_msg}",
            "is_active": coupon.is_active
        })


# ────────────────────────────────────────────────
# Coupon Statistics
# ────────────────────────────────────────────────
class CouponStatsAPIView(APIView):
    """
    Get coupon usage statistics summary
    """
    permission_classes = [IsAuthenticated, IsTenantAdmin]

    @swagger_auto_schema(
        operation_summary="Coupon statistics summary",
        tags=["Coupons"]
    )
    def get(self, request):
        user = request.user
        now = timezone.now()

        if user.is_superadmin:
            queryset = Coupon.objects.all()
        else:
            if not user.organization:
                return Response({"error": "No store associated with this user"}, status=400)
            queryset = Coupon.objects.filter(organization=user.organization)

        stats = {
            "total": queryset.count(),
            "active": queryset.filter(is_active=True, valid_to__gt=now, valid_from__lte=now).count(),
            "expired": queryset.filter(Q(valid_to__lte=now) | Q(is_expired=True)).count(),
            "upcoming": queryset.filter(is_active=True, valid_from__gt=now).count(),
            "inactive": queryset.filter(is_active=False).count()
        }
        return Response(stats)


# admin_core/api_views/schedule_control.py

class ToggleScheduleAPIView(APIView):
    # permission_classes = [IsAdminUser]

    def post(self, request):
        task_name = request.data.get("task_name")
        action = request.data.get("action")  # "on" | "off"

        if not task_name or action not in ["on", "off"]:
            return Response(
                {"error": "task_name and valid action required"},
                status=400
            )

        try:
            task = PeriodicTask.objects.get(name=task_name)
        except PeriodicTask.DoesNotExist:
            return Response({"error": "Task not found"}, status=404)

        # toggle
        task.enabled = True if action == "on" else False
        task.save(update_fields=["enabled"])

        return Response({
            "task": task.name,
            "enabled": task.enabled,
            "message": f"Schedule turned {action.upper()}"
        })


class DashboardSchedulerControlAPIView(APIView):
    # permission_classes = [IsAdminUser]

    def get(self, request):
        """Current status of the dashboard scheduler"""
        task = PeriodicTask.objects.filter(
            name='update-active-merchant-dashboards-every-minute'
        ).first()

        if not task:
            return Response({"error": "Scheduler not found"}, status=404)

        return Response({
            "name": task.name,
            "enabled": task.enabled,
            "last_run_at": task.last_run_at.isoformat() if task.last_run_at else None,
            "total_run_count": task.total_run_count,
        })

    def post(self, request):
        """Turn on / off the scheduler"""
        action = request.data.get("action")  # "enable" or "disable"

        if action not in ["enable", "disable"]:
            return Response({"error": "action must be 'enable' or 'disable'"}, status=400)

        task = PeriodicTask.objects.filter(
            name='update-active-merchant-dashboards-every-minute'
        ).first()

        if not task:
            return Response({"error": "Scheduler not found"}, status=404)

        task.enabled = (action == "enable")
        task.save()

        return Response({
            "message": f"Scheduler {action}d successfully",
            "enabled": task.enabled
        })


