
# billing/views.py 
# Changed from ViewSet + routers to pure APIView + function-based or class-based without router dependency
# All logic preserved, just restructured to use APIView / @api_view style
# This makes it compatible with your existing project style (no routers, explicit URL patterns)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.conf import settings
import stripe
from stripe import StripeError
from django.db import transaction

from django.utils import timezone
# from store.models import Product
from django.db.models import Q


from billing.services import create_proration_invoice
from billing.utils import calculate_proration
from merchant_user.models import Organization
from .permissions import AdminGetMerchantGetAdminPostOnly,IsAdminUserOnly
from .models import (
    SubscriptionPlan,
    OrganizationSubscription,
    ProductBoostSubscription,
    CustomerSubscription
    
)
from global_payments.models import Invoice
from .serializers import (
    SubscriptionPlanSerializer,
    OrganizationSubscriptionSerializer,
    ProductBoostSubscriptionSerializer,
    InvoiceSerializer
)


stripe.api_key = settings.STRIPE_SECRET_KEY


class AdminSubscriptionPlanListCreateAPIView(APIView):
    permission_classes = [AdminGetMerchantGetAdminPostOnly]

    def get(self, request):
        plans = SubscriptionPlan.objects.all()
        serializer = SubscriptionPlanSerializer(plans, many=True)
        # print(serializer.data)
        return Response(serializer.data)

    def post(self, request):
        print(100)
        serializer = SubscriptionPlanSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminSubscriptionPlanDetailAPIView(APIView):
    permission_classes = [IsAdminUserOnly]

    def get(self, request, pk):
        plan = get_object_or_404(SubscriptionPlan, pk=pk)
        serializer = SubscriptionPlanSerializer(plan)
        return Response(serializer.data)

    def put(self, request, pk):
        plan = get_object_or_404(SubscriptionPlan, pk=pk)
        old_plan_level = plan.plan_level 
        serializer = SubscriptionPlanSerializer(plan, data=request.data, partial=True)
        if serializer.is_valid():
                with transaction.atomic():
                    updated_plan = serializer.save()

                    # যদি plan_level change হয়
                    new_plan_level = updated_plan.plan_level
                    # print(f"Plan level changed from {old_plan_level} to {new_plan_level} for Plan ID: {updated_plan.id}")
                    if old_plan_level != new_plan_level:
                        Organization.objects.filter(
                            subscription_plan_level=old_plan_level,
                            subscription_status='active'
                        ).update(subscription_plan_level=new_plan_level)
                
                return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        plan = get_object_or_404(SubscriptionPlan, pk=pk)
        plan.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

class AdminOrganizationSubscriptionListAPIView(APIView):
    permission_classes = [IsAdminUserOnly]

    def get(self, request):
        qs = OrganizationSubscription.objects.select_related('organization', 'plan')
        serializer = OrganizationSubscriptionSerializer(qs, many=True)
        return Response(serializer.data)


class AdminOrganizationSubscriptionDetailAPIView(APIView):
    permission_classes = [IsAdminUserOnly]

    def get(self, request, pk):
        sub = get_object_or_404(OrganizationSubscription, pk=pk)
        serializer = OrganizationSubscriptionSerializer(sub)
        return Response(serializer.data)

    def patch(self, request, pk):
        """
        Admin can change status: active / cancelled / expired
        """
        sub = get_object_or_404(OrganizationSubscription, pk=pk)
        status_value = request.data.get("status")

        if status_value:
            sub.status = status_value
            sub.save()

        serializer = OrganizationSubscriptionSerializer(sub)
        return Response(serializer.data)
    

class AdminProductBoostListAPIView(APIView):
    permission_classes = [IsAdminUserOnly]

    def get(self, request):
        boosts = ProductBoostSubscription.objects.select_related(
            'organization_subscription'
        )
        serializer = ProductBoostSubscriptionSerializer(boosts, many=True)
        return Response(serializer.data)

class AdminProductBoostDetailAPIView(APIView):
    permission_classes = [IsAdminUserOnly]

    def patch(self, request, pk):
        boost = get_object_or_404(ProductBoostSubscription, pk=pk)
        boost.is_active = False
        boost.save()
        serializer = ProductBoostSubscriptionSerializer(boost)
        return Response(serializer.data)
    

class AdminInvoiceListAPIView(APIView):
    permission_classes = [IsAdminUserOnly]

    def get(self, request):
        invoices = Invoice.objects.select_related('organization')
        serializer = InvoiceSerializer(invoices, many=True)
        return Response(serializer.data)

class AdminInvoiceDetailAPIView(APIView):
    permission_classes = [IsAdminUserOnly]

    def patch(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk)
        status_value = request.data.get("status")

        if status_value == "paid":
            invoice.status = "paid"
            invoice.paid_at = timezone.now()
        elif status_value in ["pending", "failed"]:
            invoice.status = status_value

        invoice.save()
        serializer = InvoiceSerializer(invoice)
        return Response(serializer.data)

class PublicOrganizationPlanListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        plans = SubscriptionPlan.objects.filter(
            plan_type='organization',
            is_active=True
        )
        serializer = SubscriptionPlanSerializer(plans, many=True)
        return Response(serializer.data)

class PlusMembershipPlanListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        plans = SubscriptionPlan.objects.filter(
            plan_type='plus_membership',
            is_active=True
        )
        serializer = SubscriptionPlanSerializer(plans, many=True)
        return Response(serializer.data)
    
    
class ProductBoostSubscriptionListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        boosts = SubscriptionPlan.objects.filter(
            plan_type='product_boost',
            is_active=True
        )
        serializer = SubscriptionPlanSerializer(boosts, many=True)
        return Response(serializer.data)

    def post(self, request):
        subscription = OrganizationSubscription.objects.filter(
            organization=request.user.organization,
            status="active"
        ).first()

        if not subscription:
            return Response({"error": "No active subscription"}, status=400)

        # Check if user has already boosted max products
        active_boosts_count = ProductBoostSubscription.objects.filter(
            organization_subscription=subscription,
            is_active=True
        ).count()

        if active_boosts_count >= subscription.plan.max_boosted_products:
            return Response({"error": "Boost limit reached"}, status=400)

        boost = ProductBoostSubscription.objects.create(
            organization_subscription=subscription,
            is_active=True
        )
        serializer = ProductBoostSubscriptionSerializer(boost)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CurrentSubscriptionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        
        subscription_type = request.query_params.get(
        "type",
        "organization"
        )
        
        # ====================================
        # ORGANIZATION SUBSCRIPTION
        # ====================================
        if subscription_type == "organization":
            organization = request.user.organization
            if not organization:
                return Response({
                    "subscription": None
                })
            

        subscriptions = (
            OrganizationSubscription.objects
            .select_related('plan')
            .filter(
                organization=organization,
                status='active',
                plan__plan_type=plan_type
            )
            .filter(
                Q(end_date__isnull=True) |
                Q(end_date__gt=timezone.now())
            )
        )
        print("Active subscriptions found:", subscriptions.count())

        subscription = subscriptions.order_by('-start_date').first()

        subscription_data = None
        # for x in subscriptions:
        #     print("Active subscription found:", x.id, "Plan:", x.plan.name, "Ends at:", x.end_date)
        #     print()
        # if subscriptions:

        #     print("Current subscription found for organization:", organization.name)

        if subscription:
            plan = subscription.plan
            print(f"Current subscription plan: {plan.name}, level: {plan.plan_level}, ends at: {subscription.end_date}")

            days_remaining = None
            if subscription.end_date:
                delta = subscription.end_date - timezone.now()
                days_remaining = max(delta.days, 0)

            subscription_data = {
                "id": subscription.id,
                "plan_id": plan.id,
                "plan_name": plan.name,
                "plan_level": plan.plan_level,
                "plan_type": plan.plan_type,
                "price": str(plan.price),
                "currency": plan.currency,
                "billing_cycle": plan.billing_cycle,
                "status": subscription.status,
                "auto_renew": subscription.auto_renew,
                "start_date": subscription.start_date,
                "end_date": subscription.end_date,
                "days_remaining": days_remaining,
                "is_expiring_soon": subscription.is_expiring_soon,
                "usage": {
                    "products_used": subscription.current_usage.get("products", 0),
                    "products_limit": plan.max_products,
                    "boosted_used": subscription.boosted_products_count,
                    "boosted_limit": plan.max_boosted_products,
                }
            }

        # 🔥 Available plans (same plan_type)
        available_plans = SubscriptionPlan.objects.filter(
            is_active=True,
            plan_type=plan_type
        ).order_by("price")

        plans_data = SubscriptionPlanSerializer(available_plans, many=True).data

        return Response({
            "subscription": subscription_data,
            "plans": plans_data
        })

class UpgradeSubscriptionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        organization = request.user.organization
        new_plan_id = request.data.get("plan_id")
        subscription = OrganizationSubscription.objects.filter(
            organization=organization, status="active"
        ).first()

        if not subscription:
            return Response({"error": "No active subscription"}, status=400)

        new_plan = get_object_or_404(SubscriptionPlan, id=new_plan_id)

        if not subscription.stripe_subscription_item_id:
            return Response({"error": "Stripe subscription item missing"}, status=500)

        try:
            # Upgrade immediately with proration
            stripe_sub = stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                items=[{
                    "id": subscription.stripe_subscription_item_id,
                    "price": new_plan.stripe_price_id,
                }],
                proration_behavior="create_prorations",
                    metadata={
                        "change_type": "upgrade",
                        "new_plan_id": new_plan.id,
                        "organization_id": organization.id
                    }
            )
            print("Stripe subscription upgraded:")
            
        except StripeError as e:
            return Response({"error": str(e)}, status=400)
       

        # Calculate proration
        proration = calculate_proration(subscription, new_plan)

        # Create invoice
        invoice = create_proration_invoice(subscription, proration)

        return Response({
            "message": "Upgrade initiated successfully",
            "stripe_subscription": stripe_sub.id
        })
   
class DowngradeAtPeriodEndAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        organization = request.user.organization
        new_plan_id = request.data.get("plan_id")
        subscription = OrganizationSubscription.objects.filter(
            organization=organization, status="active"
        ).first()

        if not subscription:
            return Response({"error": "No active subscription"}, status=400)

        new_plan = get_object_or_404(SubscriptionPlan, id=new_plan_id)

        # Already scheduled?
        if getattr(subscription, "downgrade_at_period_end", None):
            return Response({"message": "Downgrade already scheduled"}, status=200)

        # Schedule downgrade at period end
        subscription.downgrade_at_period_end = True
        subscription.downgrade_plan_id = new_plan.id
        subscription.save(update_fields=["downgrade_at_period_end", "downgrade_plan_id"])

        # Update Stripe metadata so webhook can detect it
        try:
            stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                metadata={
                    "change_type": "downgrade",
                    "new_plan_id": new_plan.id,
                    "organization_id": organization.id
                }
            )
        except stripe.error.StripeError as e:
            print("Stripe metadata update failed:", e)

        return Response({
            "message": f"Downgrade to {new_plan.name} scheduled at period end",
            "current_access_until": subscription.end_date
        })
    

class CancelSubscriptionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        organization = request.user.organization

        subscription = OrganizationSubscription.objects.filter(
            organization=organization,
            status="active"
        ).first()
        # print("Cancel subscription request for:", subscription)

        if not subscription:
            return Response({"error": "No active subscription"}, status=400)

        if getattr(subscription, "cancel_at_period_end", False):
            return Response(
                {"message": "Subscription already scheduled for cancellation"},
                status=200
            )

        # Stripe এ cancel at period end সেট করা
        try:
            stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                cancel_at_period_end=True
            )
        except StripeError as e:
            return Response({"error": str(e)}, status=400)

        # Local DB update
        subscription.cancel_at_period_end = True
        subscription.status = "cancelled"
        subscription.save(update_fields=["cancel_at_period_end", "status"])
        organization.subscription_status = "cancelled"
        # print("Organization subscription status updated to cancelled for:", organization.name)
        organization.save(update_fields=["subscription_status"])
        print("Organization subscription status:", organization.subscription_status)


        return Response({
            "message": "Subscription will cancel at period end",
            "access_until": subscription.end_date
        })
    
class SubscriptionProrationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        organization = request.user.organization
        new_plan_id = request.data.get("plan_id")
        subscription = OrganizationSubscription.objects.filter(
            organization=organization, status="active"
        ).first()

        if not subscription:
            return Response({"error": "No active subscription"}, status=400)

        new_plan = get_object_or_404(SubscriptionPlan, id=new_plan_id)
        proration = calculate_proration(subscription, new_plan)

        return Response(proration)


class MembershipStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        is_plus_member = CustomerSubscription.objects.filter(
            user=request.user,
            status="active"
        ).exists()

        return Response({
            "is_plus_member": is_plus_member
        })
 
    