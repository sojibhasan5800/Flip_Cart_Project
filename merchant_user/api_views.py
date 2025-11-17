
from rest_framework import status, generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny,IsAuthenticated
from django.utils import timezone
from datetime import timedelta
import stripe
from django.conf import settings
from merchant_user.models import Tenant
from merchant_user.serializers import (MerchantRegistrationSerializer,TenantSerializer,SubscriptionSerializer,
                                       MerchantUserRegistrationSerializer,TenantAccountSerializer)
from accounts.serializers import  AccountSerializer



class MerchantRegistrationAPIView(APIView):
    """
    Merchant registration with automatic Stripe subscription
    POST /api/accounts/merchant/register/
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = MerchantRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            validated_data = serializer.validated_data
            business_name = validated_data['business_name']
            subdomain = validated_data['subdomain']
            email = validated_data['email']
            
            try:
                # Create tenant
                tenant = Tenant.objects.create(
                    name=business_name,
                    subdomain=subdomain,
                    email=email,
                    phone=validated_data['phone'],
                    is_trial=True,
                    trial_ends_at=timezone.now() + timedelta(days=14)
                )
                
                # Stripe integration
                stripe.api_key = settings.STRIPE_SECRET_KEY
                
                # Create Stripe customer
                stripe_customer = stripe.Customer.create(
                    email=email,
                    name=business_name,
                    metadata={
                        'tenant_id': str(tenant.id),
                        'subdomain': subdomain,
                        'type': 'merchant'
                    }
                )
                
                # Create subscription with trial
                subscription = stripe.Subscription.create(
                    customer=stripe_customer.id,
                    items=[{
                        'price': settings.STRIPE_PLANS['basic']['price_id']
                    }],
                    trial_period_days=14,
                    metadata={
                        'tenant_id': str(tenant.id),
                        'subdomain': subdomain
                    }
                )
                
                # Update tenant with Stripe info
                tenant.stripe_customer_id = stripe_customer.id
                tenant.stripe_subscription_id = subscription.id
                tenant.save()
                
                # Create merchant owner account using UserRegistrationSerializer
                user_data = {
                    'first_name': validated_data['first_name'],
                    'last_name': validated_data['last_name'],
                    'email': email,
                    'phone_number': validated_data['phone'],
                    'password': validated_data['password'],
                    'confirm_password': validated_data['confirm_password']
                }
                
                user_serializer = MerchantUserRegistrationSerializer(
                    data=user_data, 
                    context={'tenant': tenant}
                )
                
                if user_serializer.is_valid():
                    user = user_serializer.save()
                    
                    response_data = {
                        'status': True,
                        'message': 'Merchant account created successfully',
                        'data': {
                            'tenant': TenantSerializer(tenant).data,
                            'user': TenantAccountSerializer(user).data,
                            'subscription': {
                                'status': 'trial',
                                'trial_ends_at': tenant.trial_ends_at,
                                'plan': 'basic'
                            },
                            'store_url': f"https://{subdomain}.flipcart.com"
                        }
                    }
                    
                    return Response(response_data, status=status.HTTP_201_CREATED)
                else:
                    tenant.delete()
                    return Response({
                        'status': False,
                        'message': 'User creation failed',
                        'errors': user_serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)
                
            except stripe.error.StripeError as e:
                if 'tenant' in locals():
                    tenant.delete()
                return Response({
                    'status': False,
                    'message': f'Payment processing failed: {str(e)}',
                    'error_code': 'STRIPE_ERROR'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            except Exception as e:
                if 'tenant' in locals():
                    tenant.delete()
                return Response({
                    'status': False,
                    'message': f'Registration failed: {str(e)}',
                    'error_code': 'REGISTRATION_ERROR'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        else:
            return Response({
                'status': False,
                'message': 'Invalid data provided',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

class MerchantDashboardAPIView(APIView):
    """
    Merchant dashboard data
    GET /api/accounts/merchant/dashboard/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if not request.user.is_merchant_user:
            return Response({
                'status': False,
                'message': 'Access denied. Merchant account required.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        tenant = request.user.tenant
        
        # Get store statistics
        from store.models import Product
        from orders.models import Order
        
        total_products = Product.objects.filter(tenant=tenant).count()
        total_orders = Order.objects.filter(tenant=tenant).count()
        active_products = Product.objects.filter(tenant=tenant, is_available=True).count()
        
        dashboard_data = {
            'tenant': TenantSerializer(tenant).data,
            'user': AccountSerializer(request.user).data,
            'stats': {
                'total_products': total_products,
                'total_orders': total_orders,
                'active_products': active_products,
            },
            'subscription': SubscriptionSerializer(tenant).data
        }
        
        return Response({
            'status': True,
            'data': dashboard_data
        })
class SubscriptionPlansAPIView(APIView):
    """
    Get available subscription plans
    GET /api/accounts/subscription/plans/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all available subscription plans"""
        plans = []
        
        for plan_key, plan_data in settings.STRIPE_PLANS.items():
            plans.append({
                'id': plan_key,
                'name': plan_data['name'],
                'price': plan_data['price'],
                'price_id': plan_data['price_id'],
                'features': plan_data.get('features', [])
            })
        
        return Response({
            'status': True,
            'data': plans
        })

class MerchantSubscriptionAPIView(APIView):
    """
    Merchant subscription management
    GET /api/accounts/merchant/subscription/ - Get subscription details
    PUT /api/accounts/merchant/subscription/ - Update subscription
    DELETE /api/accounts/merchant/subscription/ - Cancel subscription
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get current subscription details"""
        if not request.user.is_merchant_user:
            return Response({
                'status': False,
                'message': 'Access denied. Merchant account required.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        tenant = request.user.tenant
        
        try:
            # Fetch latest subscription data from Stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY
            
            subscription_data = {}
            
            if tenant.stripe_subscription_id:
                subscription = stripe.Subscription.retrieve(tenant.stripe_subscription_id)
                subscription_data = {
                    'stripe_status': subscription.status,
                    'current_period_start': subscription.current_period_start,
                    'current_period_end': subscription.current_period_end,
                    'cancel_at_period_end': subscription.cancel_at_period_end,
                }
            
            subscription_info = SubscriptionSerializer(tenant).data
            subscription_info.update(subscription_data)
            
            return Response({
                'status': True,
                'data': subscription_info
            })
            
        except stripe.error.StripeError as e:
            return Response({
                'status': False,
                'message': f'Failed to fetch subscription details: {str(e)}',
                'error_code': 'STRIPE_ERROR'
            }, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        """Update subscription plan"""
        if not request.user.is_merchant_user:
            return Response({
                'status': False,
                'message': 'Access denied. Merchant account required.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        plan_type = request.data.get('plan_type')  # 'basic', 'premium', etc.
        
        if not plan_type or plan_type not in settings.STRIPE_PLANS:
            return Response({
                'status': False,
                'message': 'Invalid plan type',
                'available_plans': list(settings.STRIPE_PLANS.keys())
            }, status=status.HTTP_400_BAD_REQUEST)
        
        tenant = request.user.tenant
        
        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            
            if not tenant.stripe_subscription_id:
                return Response({
                    'status': False,
                    'message': 'No active subscription found'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update subscription
            subscription = stripe.Subscription.retrieve(tenant.stripe_subscription_id)
            
            updated_subscription = stripe.Subscription.modify(
                tenant.stripe_subscription_id,
                items=[{
                    'id': subscription['items']['data'][0].id,
                    'price': settings.STRIPE_PLANS[plan_type]['price_id']
                }],
                proration_behavior='create_prorations'
            )
            
            return Response({
                'status': True,
                'message': f'Subscription updated to {plan_type} plan',
                'data': {
                    'plan': plan_type,
                    'status': updated_subscription.status,
                    'current_period_end': updated_subscription.current_period_end
                }
            })
            
        except stripe.error.StripeError as e:
            return Response({
                'status': False,
                'message': f'Failed to update subscription: {str(e)}',
                'error_code': 'STRIPE_ERROR'
            }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """Cancel subscription (at period end)"""
        if not request.user.is_merchant_user:
            return Response({
                'status': False,
                'message': 'Access denied. Merchant account required.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        tenant = request.user.tenant
        
        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            
            if not tenant.stripe_subscription_id:
                return Response({
                    'status': False,
                    'message': 'No active subscription found'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Cancel subscription at period end
            canceled_subscription = stripe.Subscription.modify(
                tenant.stripe_subscription_id,
                cancel_at_period_end=True
            )
            
            return Response({
                'status': True,
                'message': 'Subscription will be canceled at the end of the billing period',
                'data': {
                    'cancel_at_period_end': canceled_subscription.cancel_at_period_end,
                    'current_period_end': canceled_subscription.current_period_end
                }
            })
            
        except stripe.error.StripeError as e:
            return Response({
                'status': False,
                'message': f'Failed to cancel subscription: {str(e)}',
                'error_code': 'STRIPE_ERROR'
            }, status=status.HTTP_400_BAD_REQUEST)

class ReactivateSubscriptionAPIView(APIView):
    """
    Reactivate canceled subscription
    POST /api/accounts/merchant/subscription/reactivate/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Reactivate a canceled subscription"""
        if not request.user.is_merchant_user:
            return Response({
                'status': False,
                'message': 'Access denied. Merchant account required.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        tenant = request.user.tenant
        
        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            
            if not tenant.stripe_subscription_id:
                return Response({
                    'status': False,
                    'message': 'No subscription found'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Reactivate subscription
            subscription = stripe.Subscription.retrieve(tenant.stripe_subscription_id)
            
            if not subscription.cancel_at_period_end:
                return Response({
                    'status': False,
                    'message': 'Subscription is not scheduled for cancellation'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            reactivated_subscription = stripe.Subscription.modify(
                tenant.stripe_subscription_id,
                cancel_at_period_end=False
            )
            
            return Response({
                'status': True,
                'message': 'Subscription reactivated successfully',
                'data': {
                    'cancel_at_period_end': reactivated_subscription.cancel_at_period_end,
                    'status': reactivated_subscription.status
                }
            })
            
        except stripe.error.StripeError as e:
            return Response({
                'status': False,
                'message': f'Failed to reactivate subscription: {str(e)}',
                'error_code': 'STRIPE_ERROR'
            }, status=status.HTTP_400_BAD_REQUEST)
