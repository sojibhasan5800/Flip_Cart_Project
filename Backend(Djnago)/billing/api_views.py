
# billing/views.py 
# Changed from ViewSet + routers to pure APIView + function-based or class-based without router dependency
# All logic preserved, just restructured to use APIView / @api_view style
# This makes it compatible with your existing project style (no routers, explicit URL patterns)

from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.conf import settings
import stripe
from django.utils import timezone
from store.models import Product
from .permissions import IsAdminUserOnly
from .models import (
    SubscriptionPlan,
    OrganizationSubscription,
    ProductBoostSubscription,
    Invoice
)
from .serializers import (
    SubscriptionPlanSerializer,
    OrganizationSubscriptionSerializer,
    ProductBoostSubscriptionSerializer,
    InvoiceSerializer
)


stripe.api_key = settings.STRIPE_SECRET_KEY


class AdminSubscriptionPlanListCreateAPIView(APIView):
    permission_classes = [IsAdminUserOnly]

    def get(self, request):
        plans = SubscriptionPlan.objects.all()
        serializer = SubscriptionPlanSerializer(plans, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = SubscriptionPlanSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





















# # ───────────────────────────────────────────────
# # Subscription Plans - List only (read-only)
# # ───────────────────────────────────────────────
# class SubscriptionPlanListAPIView(APIView):
#     """
#     GET: List all active subscription plans
#     """
#     def get(self, request):
#         plans = SubscriptionPlan.objects.filter(is_active=True)
#         serializer = SubscriptionPlanSerializer(plans, many=True)
#         return Response(serializer.data)


# # ───────────────────────────────────────────────
# # Organization Subscriptions
# # ───────────────────────────────────────────────
# class OrganizationSubscriptionListCreateAPIView(APIView):
#     """
#     GET: List current merchant's subscriptions
#     POST: Create new subscription (with Stripe)
#     """
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         try:
#             org = request.user.merchant_profile.first().organization
#         except AttributeError:
#             return Response({"error": "User has no merchant profile"}, status=status.HTTP_403_FORBIDDEN)

#         subscriptions = OrganizationSubscription.objects.filter(organization=org)
#         serializer = OrganizationSubscriptionSerializer(subscriptions, many=True)
#         return Response(serializer.data)

#     def post(self, request):
#         try:
#             org = request.user.merchant_profile.first().organization
#         except AttributeError:
#             return Response({"error": "User has no merchant profile"}, status=status.HTTP_403_FORBIDDEN)

#         plan_slug = request.data.get('plan_slug')
#         if not plan_slug:
#             return Response({"error": "plan_slug is required"}, status=status.HTTP_400_BAD_REQUEST)

#         plan = get_object_or_404(SubscriptionPlan, slug=plan_slug)

#         try:
#             stripe_sub = stripe.Subscription.create(
#                 customer=org.stripe_customer_id,
#                 items=[{'price': plan.stripe_price_id}],
#                 payment_behavior='default_incomplete',
#                 expand=['latest_invoice.payment_intent'],
#             )

#             subscription = OrganizationSubscription.objects.create(
#                 organization=org,
#                 plan=plan,
#                 stripe_subscription_id=stripe_sub.id,
#                 stripe_customer_id=org.stripe_customer_id,
#             )

#             Invoice.objects.create(
#                 organization=org,
#                 subscription=subscription,
#                 amount=plan.price,
#                 stripe_invoice_id=stripe_sub.latest_invoice.id
#             )

#             serializer = OrganizationSubscriptionSerializer(subscription)
#             return Response(serializer.data, status=status.HTTP_201_CREATED)

#         except stripe.error.StripeError as e:
#             return Response({"error": str(e.user_message or str(e))}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             return Response({"error": "Internal error during subscription creation"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def subscription_upgrade_downgrade(request, subscription_id):
#     """
#     POST: Upgrade or downgrade existing subscription
#     Body: {"new_plan_slug": "pro"}
#     """
#     subscription = get_object_or_404(OrganizationSubscription, id=subscription_id)

#     # Security: only owner of this subscription
#     if subscription.organization != request.user.merchant_profile.first().organization:
#         return Response({"error": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)

#     new_plan_slug = request.data.get('new_plan_slug')
#     if not new_plan_slug:
#         return Response({"error": "new_plan_slug is required"}, status=status.HTTP_400_BAD_REQUEST)

#     new_plan = get_object_or_404(SubscriptionPlan, slug=new_plan_slug)

#     try:
#         subscription.upgrade(new_plan)  # your model method
#         return Response({"message": "Plan change processed successfully"}, status=status.HTTP_200_OK)
#     except Exception as e:
#         return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def subscription_invoices_list(request):
#     """
#     GET: List all invoices of the current merchant
#     """
#     try:
#         org = request.user.merchant_profile.first().organization
#     except AttributeError:
#         return Response({"error": "User has no merchant profile"}, status=status.HTTP_403_FORBIDDEN)

#     invoices = Invoice.objects.filter(organization=org).order_by('-issued_at')
#     serializer = InvoiceSerializer(invoices, many=True)
#     return Response(serializer.data)


# # ───────────────────────────────────────────────
# # Product Boost Subscriptions
# # ───────────────────────────────────────────────
# class ProductBoostSubscriptionListCreateAPIView(APIView):
#     """
#     GET: List current merchant's product boosts
#     POST: Create new product boost (with Stripe charge)
#     """
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         try:
#             org = request.user.merchant_profile.first().organization
#         except AttributeError:
#             return Response({"error": "No merchant profile"}, status=status.HTTP_403_FORBIDDEN)

#         boosts = ProductBoostSubscription.objects.filter(
#             organization_subscription__organization=org
#         )
#         serializer = ProductBoostSubscriptionSerializer(boosts, many=True)
#         return Response(serializer.data)

#     def post(self, request):
#         try:
#             org = request.user.merchant_profile.first().organization
#         except AttributeError:
#             return Response({"error": "No merchant profile"}, status=status.HTTP_403_FORBIDDEN)

#         org_sub_id = request.data.get('organization_subscription')
#         product_id = request.data.get('product')
#         priority_level = request.data.get('priority_level', 1)
#         stripe_token = request.data.get('stripe_token')  # required for charge

#         if not all([org_sub_id, product_id, stripe_token]):
#             return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

#         org_sub = get_object_or_404(OrganizationSubscription, id=org_sub_id, organization=org)
#         product = get_object_or_404(Product, id=product_id, organization=org)

#         if not org_sub.can_boost_more():
#             return Response({"error": "Boost limit reached for this plan"}, status=status.HTTP_400_BAD_REQUEST)

#         plan = org_sub.plan  # or you can have separate boosting plan

#         try:
#             charge = stripe.Charge.create(
#                 amount=int(plan.price * 100),  # Adjust logic: per-boost fee or plan-based
#                 currency=plan.currency,
#                 description=f"Product boost: {product.product_name}",
#                 source=stripe_token,
#                 customer=org_sub.stripe_customer_id,
#             )

#             boost = ProductBoostSubscription.objects.create(
#                 product=product,
#                 organization_subscription=org_sub,
#                 boost_end_date=timezone.now() + timezone.timedelta(days=plan.duration_days),
#                 priority_level=priority_level
#             )

#             product.is_boosted = True
#             product.boost_priority = boost.priority_level
#             product.save()

#             # Optional: create invoice for this boost
#             Invoice.objects.create(
#                 organization=org,
#                 subscription=org_sub,
#                 amount=plan.price / 10,  # example per-boost fee
#                 line_items=[{"description": f"Boost: {product.product_name}", "amount": plan.price / 10}]
#             )

#             serializer = ProductBoostSubscriptionSerializer(boost)
#             return Response(serializer.data, status=status.HTTP_201_CREATED)

#         except stripe.error.StripeError as e:
#             return Response({"error": str(e.user_message or str(e))}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             return Response({"error": "Failed to create boost"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# # ... existing imports ...

# # from payments.models import PaymentTransaction
# # from payments.tasks import verify_payment

# # ... existing views ...

# # # New: Plan Purchase View (integrate with payments app)
# # class SubscriptionPlanPurchaseAPIView(APIView):
# #     permission_classes = [IsAuthenticated]

# #     def post(self, request):
# #         org = request.user.merchant_profile.first().organization
# #         plan_slug = request.data.get('plan_slug')
# #         gateway = request.data.get('gateway')
# #         stripe_token = request.data.get('stripe_token') if gateway == 'stripe' else None

# #         plan = get_object_or_404(SubscriptionPlan, slug=plan_slug)

# #         # Create payment transaction via payments app
# #         trans = PaymentTransaction.objects.create(
# #             organization=org,
# #             amount=plan.price,
# #             currency=plan.currency,
# #             gateway=gateway,
# #             metadata={'plan_id': plan.id, 'type': 'subscription_purchase'}
# #         )

# #         try:
# #             if gateway == 'stripe':
# #                 intent = stripe.PaymentIntent.create(
# #                     amount=int(plan.price * 100),
# #                     currency=plan.currency.lower(),
# #                     description=f"Purchase {plan.name} Plan",
# #                     customer=org.stripe_customer_id,
# #                 )
# #                 trans.gateway_transaction_id = intent.id
# #                 trans.save()
# #                 return Response({"client_secret": intent.client_secret})  # Frontend confirm

# #             elif gateway == 'bkash':
# #                 # bKash session create (from payments/views.py logic, reuse or call)
# #                 # ... similar to payments CreatePaymentIntent ...
# #                 # Return bkash_url

# #         except Exception as e:
# #             trans.status = 'failed'
# #             trans.save()
# #             return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# # # Update webhook in payments to handle plan purchase
# # # In payments/views.py PaymentWebhook: add logic for 'type': 'subscription_purchase'
# # if trans.metadata.get('type') == 'subscription_purchase':
# #     plan = SubscriptionPlan.objects.get(id=trans.metadata['plan_id'])
# #     sub = OrganizationSubscription.objects.create(
# #         organization=trans.organization,
# #         plan=plan,
# #         stripe_subscription_id=trans.gateway_transaction_id if trans.gateway == 'stripe' else '',
# #     )
# #     # Invoice create, etc.

# # ... rest existing ...
