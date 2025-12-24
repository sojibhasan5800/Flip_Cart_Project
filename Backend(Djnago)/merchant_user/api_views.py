
# from rest_framework import status, generics, permissions
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import AllowAny,IsAuthenticated
# from django.utils import timezone
# from datetime import timedelta
# import stripe
# from django.conf import settings
# from merchant_user.models import Organization,StoreProfile
# from merchant_user.serializers import (MerchantRegistrationSerializer,TenantSerializer,SubscriptionSerializer,
#                                        MerchantUserRegistrationSerializer,TenantAccountSerializer,StoreCreateSerializer
#                                        ,StoreStatusSerializer)
# from accounts.serializers import  AccountSerializer
# from django.db import transaction
# from django_tenants.utils import schema_context
# from delivery_system.models import DeliveryTenant,DeliveryDomain
# from django.core.management import call_command

# import store



# class MerchantRegistrationAPIView(APIView):
#     """
#     Merchant registration with automatic Stripe subscription
#     POST /api/accounts/merchant/register/
#     """
#     permission_classes = [AllowAny]

#     def post(self, request):
#         serializer = MerchantRegistrationSerializer(data=request.data)

#         # 1. Validate input
#         if serializer.is_valid():
#             validated_data = serializer.validated_data
#             business_name = validated_data['business_name']
#             subdomain = validated_data['subdomain']
#             email = validated_data['email']

#             try:
#                 # 2. Create tenant inside atomic transaction (ensures DB safety)
#                 with transaction.atomic():

#                     # 2.1 Create Organization
#                     organization = Organization.objects.create(
#                         name=business_name,
#                         subdomain=subdomain,
#                         email=email,
#                         phone=validated_data['phone'],
#                         is_trial=True,
#                         trial_ends_at=timezone.now() + timedelta(days=14)
#                     )

#                     # 2.2 Create Delivery Tenant
#                     delivery_tenant = DeliveryTenant.objects.create(
#                         name=business_name,
#                         schema_name=subdomain,  
#                         # ← Very important! Schema name must match subdomain.
#                         description=f"Delivery system for {business_name}",
#                         default_delivery_charge=60.00,
#                         free_delivery_threshold=1000.00,
#                         is_active=True
#                     )

#                     # 2.3 Create Delivery Domain
#                     DeliveryDomain.objects.create(
#                         domain=f"{subdomain}.flipcart.com",
#                         # If using localhost for testing: {subdomain}.localhost
#                         tenant=delivery_tenant,
#                         is_primary=True
#                     )

#                     # 2.4 Link Organization ↔ DeliveryTenant
#                     organization.delivery_tenant = delivery_tenant
#                     organization.save()

#                     # 2.5 Create tenant schema
#                     delivery_tenant.create_schema(check_if_exists=True)

#                     # 2.6 Switch to new tenant schema and run migrations
#                     with schema_context(delivery_tenant.schema_name):
#                         call_command('migrate', '--noinput')

#                         # Optional: Seed default delivery data
#                         call_command('seed_delivery_data')

#                 # 3. Stripe Integration
#                 stripe.api_key = settings.STRIPE_SECRET_KEY

#                 # 3.1 Create Stripe Customer
#                 stripe_customer = stripe.Customer.create(
#                     email=email,
#                     name=business_name,
#                     metadata={
#                         'organization_id': str(organization.id),
#                         'subdomain': subdomain,
#                         'type': 'merchant'
#                     }
#                 )

#                 # 3.2 Create Subscription with free trial
#                 subscription = stripe.Subscription.create(
#                     customer=stripe_customer.id,
#                     items=[{
#                         'price': settings.STRIPE_PLANS['basic']['price_id']
#                     }],
#                     trial_period_days=14,
#                     metadata={
#                         'organization_id': str(organization.id),
#                         'subdomain': subdomain
#                     }
#                 )

#                 # 3.3 Save Stripe data in Organization
#                 organization.stripe_customer_id = stripe_customer.id
#                 organization.stripe_subscription_id = subscription.id
#                 organization.save()

#                 # 4. Create Merchant Owner Account
#                 user_data = {
#                     'first_name': validated_data['first_name'],
#                     'last_name': validated_data['last_name'],
#                     'email': email,
#                     'phone_number': validated_data['phone'],
#                     'password': validated_data['password'],
#                     'confirm_password': validated_data['confirm_password']
#                 }

#                 user_serializer = MerchantUserRegistrationSerializer(
#                     data=user_data,
#                     context={'organization': organization}
#                 )

#                 # 4.1 Validate and Save Merchant Owner User
#                 if user_serializer.is_valid():
#                     user = user_serializer.save()

#                     # 5. Return success response
#                     response_data = {
#                         'status': True,
#                         'message': 'Merchant account created successfully',
#                         'data': {
#                             'organization': TenantSerializer(organization).data,
#                             'user': TenantAccountSerializer(user).data,
#                             'subscription': {
#                                 'status': 'trial',
#                                 'trial_ends_at': organization.trial_ends_at,
#                                 'plan': 'basic'
#                             },
#                             'store_url': f"https://{subdomain}.flipcart.com"
#                         }
#                     }

#                     return Response(response_data, status=status.HTTP_201_CREATED)

#                 # If user creation fails → delete Organization + revert
#                 else:
#                     organization.delete()
#                     return Response({
#                         'status': False,
#                         'message': 'User creation failed',
#                         'errors': user_serializer.errors
#                     }, status=status.HTTP_400_BAD_REQUEST)

#             # Stripe related errors
#             except stripe.error.StripeError as e:
#                 if 'organization' in locals():
#                     organization.delete()
#                 return Response({
#                     'status': False,
#                     'message': f'Payment processing failed: {str(e)}',
#                     'error_code': 'STRIPE_ERROR'
#                 }, status=status.HTTP_400_BAD_REQUEST)

#             # General errors
#             except Exception as e:
#                 if 'organization' in locals():
#                     organization.delete()
#                 return Response({
#                     'status': False,
#                     'message': f'Registration failed: {str(e)}',
#                     'error_code': 'REGISTRATION_ERROR'
#                 }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#         # Invalid initial data
#         return Response({
#             'status': False,
#             'message': 'Invalid data provided',
#             'errors': serializer.errors
#         }, status=status.HTTP_400_BAD_REQUEST)

# class MerchantDashboardAPIView(APIView):
#     """
#     Merchant dashboard data
#     GET /api/accounts/merchant/dashboard/
#     """
#     permission_classes = [IsAuthenticated]
    
#     def get(self, request):
#         if not request.user.is_merchant_user:
#             return Response({
#                 'status': False,
#                 'message': 'Access denied. Merchant account required.'
#             }, status=status.HTTP_403_FORBIDDEN)
        
#         organization = request.user.organization
        
#         # Get store statistics
#         from store.models import Product
#         from orders.models import Order
        
#         total_products = Product.objects.filter(organization=organization).count()
#         total_orders = Order.objects.filter(organization=organization).count()
#         active_products = Product.objects.filter(organization=organization, is_available=True).count()
        
#         dashboard_data = {
#             'organization': TenantSerializer(organization).data,
#             'user': AccountSerializer(request.user).data,
#             'stats': {
#                 'total_products': total_products,
#                 'total_orders': total_orders,
#                 'active_products': active_products,
#             },
#             'subscription': SubscriptionSerializer(organization).data
#         }
        
#         return Response({
#             'status': True,
#             'data': dashboard_data
#         })
# class SubscriptionPlansAPIView(APIView):
#     """
#     Get available subscription plans
#     GET /api/accounts/subscription/plans/
#     """
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         """Get all available subscription plans"""
#         plans = []
        
#         for plan_key, plan_data in settings.STRIPE_PLANS.items():
#             plans.append({
#                 'id': plan_key,
#                 'name': plan_data['name'],
#                 'price': plan_data['price'],
#                 'price_id': plan_data['price_id'],
#                 'features': plan_data.get('features', [])
#             })
        
#         return Response({
#             'status': True,
#             'data': plans
#         })

# class MerchantSubscriptionAPIView(APIView):
#     """
#     Merchant subscription management
#     GET /api/accounts/merchant/subscription/ - Get subscription details
#     PUT /api/accounts/merchant/subscription/ - Update subscription
#     DELETE /api/accounts/merchant/subscription/ - Cancel subscription
#     """
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         """Get current subscription details"""
#         if not request.user.is_merchant_user:
#             return Response({
#                 'status': False,
#                 'message': 'Access denied. Merchant account required.'
#             }, status=status.HTTP_403_FORBIDDEN)
        
#         organization = request.user.organization
        
#         try:
#             # Fetch latest subscription data from Stripe
#             stripe.api_key = settings.STRIPE_SECRET_KEY
            
#             subscription_data = {}
            
#             if organization.stripe_subscription_id:
#                 subscription = stripe.Subscription.retrieve(organization.stripe_subscription_id)
#                 subscription_data = {
#                     'stripe_status': subscription.status,
#                     'current_period_start': subscription.current_period_start,
#                     'current_period_end': subscription.current_period_end,
#                     'cancel_at_period_end': subscription.cancel_at_period_end,
#                 }
            
#             subscription_info = SubscriptionSerializer(organization).data
#             subscription_info.update(subscription_data)
            
#             return Response({
#                 'status': True,
#                 'data': subscription_info
#             })
            
#         except stripe.error.StripeError as e:
#             return Response({
#                 'status': False,
#                 'message': f'Failed to fetch subscription details: {str(e)}',
#                 'error_code': 'STRIPE_ERROR'
#             }, status=status.HTTP_400_BAD_REQUEST)

#     def put(self, request):
#         """Update subscription plan"""
#         if not request.user.is_merchant_user:
#             return Response({
#                 'status': False,
#                 'message': 'Access denied. Merchant account required.'
#             }, status=status.HTTP_403_FORBIDDEN)
        
#         plan_type = request.data.get('plan_type')  # 'basic', 'premium', etc.
        
#         if not plan_type or plan_type not in settings.STRIPE_PLANS:
#             return Response({
#                 'status': False,
#                 'message': 'Invalid plan type',
#                 'available_plans': list(settings.STRIPE_PLANS.keys())
#             }, status=status.HTTP_400_BAD_REQUEST)
        
#         organization = request.user.organization
        
#         try:
#             stripe.api_key = settings.STRIPE_SECRET_KEY
            
#             if not organization.stripe_subscription_id:
#                 return Response({
#                     'status': False,
#                     'message': 'No active subscription found'
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             # Update subscription
#             subscription = stripe.Subscription.retrieve(organization.stripe_subscription_id)
            
#             updated_subscription = stripe.Subscription.modify(
#                 organization.stripe_subscription_id,
#                 items=[{
#                     'id': subscription['items']['data'][0].id,
#                     'price': settings.STRIPE_PLANS[plan_type]['price_id']
#                 }],
#                 proration_behavior='create_prorations'
#             )
            
#             return Response({
#                 'status': True,
#                 'message': f'Subscription updated to {plan_type} plan',
#                 'data': {
#                     'plan': plan_type,
#                     'status': updated_subscription.status,
#                     'current_period_end': updated_subscription.current_period_end
#                 }
#             })
            
#         except stripe.error.StripeError as e:
#             return Response({
#                 'status': False,
#                 'message': f'Failed to update subscription: {str(e)}',
#                 'error_code': 'STRIPE_ERROR'
#             }, status=status.HTTP_400_BAD_REQUEST)

#     def delete(self, request):
#         """Cancel subscription (at period end)"""
#         if not request.user.is_merchant_user:
#             return Response({
#                 'status': False,
#                 'message': 'Access denied. Merchant account required.'
#             }, status=status.HTTP_403_FORBIDDEN)
        
#         organization = request.user.organization
        
#         try:
#             stripe.api_key = settings.STRIPE_SECRET_KEY
            
#             if not organization.stripe_subscription_id:
#                 return Response({
#                     'status': False,
#                     'message': 'No active subscription found'
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             # Cancel subscription at period end
#             canceled_subscription = stripe.Subscription.modify(
#                 organization.stripe_subscription_id,
#                 cancel_at_period_end=True
#             )
            
#             return Response({
#                 'status': True,
#                 'message': 'Subscription will be canceled at the end of the billing period',
#                 'data': {
#                     'cancel_at_period_end': canceled_subscription.cancel_at_period_end,
#                     'current_period_end': canceled_subscription.current_period_end
#                 }
#             })
            
#         except stripe.error.StripeError as e:
#             return Response({
#                 'status': False,
#                 'message': f'Failed to cancel subscription: {str(e)}',
#                 'error_code': 'STRIPE_ERROR'
#             }, status=status.HTTP_400_BAD_REQUEST)

# class ReactivateSubscriptionAPIView(APIView):
#     """
#     Reactivate canceled subscription
#     POST /api/accounts/merchant/subscription/reactivate/
#     """
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         """Reactivate a canceled subscription"""
#         if not request.user.is_merchant_user:
#             return Response({
#                 'status': False,
#                 'message': 'Access denied. Merchant account required.'
#             }, status=status.HTTP_403_FORBIDDEN)
        
#         organization = request.user.organization
        
#         try:
#             stripe.api_key = settings.STRIPE_SECRET_KEY
            
#             if not organization.stripe_subscription_id:
#                 return Response({
#                     'status': False,
#                     'message': 'No subscription found'
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             # Reactivate subscription
#             subscription = stripe.Subscription.retrieve(organization.stripe_subscription_id)
            
#             if not subscription.cancel_at_period_end:
#                 return Response({
#                     'status': False,
#                     'message': 'Subscription is not scheduled for cancellation'
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             reactivated_subscription = stripe.Subscription.modify(
#                 organization.stripe_subscription_id,
#                 cancel_at_period_end=False
#             )
            
#             return Response({
#                 'status': True,
#                 'message': 'Subscription reactivated successfully',
#                 'data': {
#                     'cancel_at_period_end': reactivated_subscription.cancel_at_period_end,
#                     'status': reactivated_subscription.status
#                 }
#             })
            
#         except stripe.error.StripeError as e:
#             return Response({
#                 'status': False,
#                 'message': f'Failed to reactivate subscription: {str(e)}',
#                 'error_code': 'STRIPE_ERROR'
#             }, status=status.HTTP_400_BAD_REQUEST)



# class CreateStoreAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         """
#         Check store status for logged-in user
#         """
#         try:         
#             # store = Storep.objects.get(owner=request.user)
#             # serializer = StoreStatusSerializer(store)
#             store = StoreProfile.objects.get(username=request.user.username)
#             serializer = StoreStatusSerializer(store)
#             return Response({
#                 "submitted": True,
#                 "data": serializer.data
#             })
#         except StoreProfile.DoesNotExist:
#             return Response({
#                 "submitted": False,
#                 "message": "No store found"
#             })

#     def post(self, request):
#         serializer = StoreCreateSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         data = serializer.validated_data

#         # org = Organization.objects.create(
#         #     name=data["name"],
#         #     subdomain=data["username"],
#         #     owner_email=data["email"],
#         #     owner_phone=data["contact"],
#         #     is_active=False
#         # )

#         StoreProfile.objects.create(
#             # organization=org,
#             username=data["username"],
#             description=data.get("description", ""),
#             address=data.get("address", ""),
#             logo_url=data.get("logo_url"),
#         )

#         return Response({
#             "status": True,
#             "message": "Store submitted for approval"
#         })
