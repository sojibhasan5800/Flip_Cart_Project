
# accounts/api/views.py
from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.shortcuts import get_object_or_404
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from rest_framework.decorators import api_view, permission_classes
from drf_yasg.utils import swagger_auto_schema
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from drf_yasg import openapi
from rest_framework.permissions import AllowAny,IsAuthenticated
from django.utils import timezone
from datetime import timedelta
import stripe
from django.conf import settings

from merchant_user.models import Organization

from .models import Account, UserProfile
from orders.models import Order, OrderProduct  # keep parity with your views (requires orders app)

from .serializers import (
    AccountSerializer,RegistrationSerializer, LoginSerializer, AccountSerializer, UserProfileSerializer
)
from django.shortcuts import redirect



#------------- previous code ------------------



# ---------------------------
# Registration API
# ---------------------------
class RegistrationAPIView(generics.CreateAPIView):
    """
    POST: Register a new user.
    - Validates password confirmation.
    - Creates a default UserProfile.
    - Sends activation email (mirrors original MVT flow).
    Edge cases:
    - Duplicate emails/usernames -> serializer validation will raise.
    Security:
    - Password returned nowhere.
    - Consider rate-limiting endpoint to reduce abuse.
    """
    serializer_class = RegistrationSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_summary="Register new user",
        tags=['Accounts'], 
        operation_description="Creates a new user account and sends activation email.",
        responses={201: openapi.Response('User created', AccountSerializer)}
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate REAL UID and Token
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        # Check custom header for API test
        is_api_test = request.headers.get('X-API-Test') == 'true'

        # response data with message + user info
        response_data = {
        "detail": "User created. Check email for activation link.",
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name
        }


        # If API test header present, include real UID/token
        if is_api_test:
            response_data.update({
                "activation_uid": uid,
                "activation_token": token,
                "activation_url": f"/api/accounts/activate/{uid}/{token}/"
            })
        
        
        # Activation email (use same template as earlier)
        # current_site = get_current_site(request)
        mail_subject = 'Please activate your account'
        message = render_to_string('accounts/account_verification_email.html', {
            'user': user,
            'base_url': settings.BASE_URL, 
            'uid': uid,
            'token': token,
            'api':True,
        })
        to_email = user.email
        try:
            EmailMessage(mail_subject, message, to=[to_email]).send()
        except Exception:
            # Non-fatal: still return created but log/notify in production
            pass
        return Response(response_data, status=status.HTTP_201_CREATED)


# ---------------------------
# Login API
from django_tenants.utils import schema_context
# ---------------------------
class LoginAPIView(APIView):
    """
    POST: Authenticate user using email + password.
    - Returns auth token for subsequent authenticated requests.
    Security:
    - Token-based auth (TokenAuthentication) used to mirror your project.
    - Consider switching to JWT/OAuth for production scale.
    """
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        request_body=LoginSerializer,
        operation_summary="Login user",
        tags=['Accounts'],
        responses={200: 'token'}
    )
    def post(self, request):

        with schema_context('public'):  #  IMPORTANT
            serializer = LoginSerializer(data=request.data)
            print("Login data received:", request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data['user']
            print("Logged in user:", user)

            refresh = RefreshToken.for_user(user)

            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": AccountSerializer(user).data
            }, status=status.HTTP_200_OK)
   

# ---------------------------
# Logout API
# ---------------------------
class LogoutAPIView(APIView):
    """
    POST: Logout user by deleting their token.
    - Requires authentication.
    Note:
    - With TokenAuthentication, logout is token deletion on server.
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
            operation_summary="Logout user",
            tags=['Accounts'],
            )
    def post(self, request):
        try:
        # blacklist all refresh tokens for user
            tokens = OutstandingToken.objects.filter(user=request.user)
            for token in tokens:
                BlacklistedToken.objects.get_or_create(token=token)
        except Exception:
            pass
        return Response({"detail": "Logged out."}, status=status.HTTP_200_OK)


from django_tenants.utils import schema_context
from django_tenants.utils import get_tenant_model

# ---------------------------
# Dashboard API
# ---------------------------

from django_tenants.utils import get_tenant_model, schema_context



class DashboardAPIView(APIView):
    """
    Role-based Dashboard API

    Roles:
    1. Super Admin  -> Platform analytics (all tenants summary)
    2. Merchant     -> Vendor dashboard (tenant specific)
    3. Customer     -> User orders & profile
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Dashboard data based on user role",
        tags=["Dashboard"]
    )
    def get(self, request):
        user = request.user

        # -----------------------------
        # 1️⃣ SUPER ADMIN DASHBOARD
        # -----------------------------
        if user.is_superadmin:
            return self._super_admin_dashboard(user)

        # -----------------------------
        # 2️⃣ MERCHANT DASHBOARD
        # -----------------------------
        if user.is_tenant_owner or user.is_tenant_staff:
            return self._merchant_dashboard(user)

        # -----------------------------
        # 3️⃣ CUSTOMER DASHBOARD
        # -----------------------------
        return self._customer_dashboard(user)

    # =====================================================
    # SUPER ADMIN DASHBOARD (PUBLIC SCHEMA ONLY)
    # =====================================================
    def _super_admin_dashboard(self, user):
        TenantModel = get_tenant_model()
        tenants = TenantModel.objects.exclude(schema_name="public")

        total_orders = 0
        total_stores = 0

        for tenant in tenants:
            try:
                with schema_context(tenant.schema_name):
                    total_orders += Order.objects.filter(is_ordered=True).count()
                    total_stores += Organization.objects.filter(is_active=True).count()
            except Exception:
                continue

        data = {
            "role": "super_admin",
            "total_tenants": tenants.count(),
            "total_orders": total_orders,
            "total_stores": total_stores, 
            "user": AccountSerializer(user).data,
        }

        return Response(data, status=status.HTTP_200_OK)

    # =====================================================
    # MERCHANT DASHBOARD (TENANT SCHEMA)
    # =====================================================
    def _merchant_dashboard(self, user):
        orders_qs = Order.objects.filter(is_ordered=True)

        data = {
            "role": "merchant",
            "total_orders": orders_qs.count(),
            "pending_orders": orders_qs.filter(status="Pending").count(),
            "completed_orders": orders_qs.filter(status="Completed").count(),
            "user": AccountSerializer(user).data,
        }

        return Response(data, status=status.HTTP_200_OK)

    # =====================================================
    # CUSTOMER DASHBOARD (TENANT SCHEMA)
    # =====================================================
    def _customer_dashboard(self, user):
        orders_qs = Order.objects.filter(
            user=user,
            is_ordered=True
        )

        userprofile, _ = UserProfile.objects.get_or_create(user=user)

        data = {
            "role": "customer",
            "orders_count": orders_qs.count(),
            "user": AccountSerializer(user).data,
            "profile": {
                "address": userprofile.full_address(),
                "city": userprofile.city,
                "country": userprofile.country,
                "profile_picture": userprofile.profile_picture.url if userprofile.profile_picture else None
            }
        }

        return Response(data, status=status.HTTP_200_OK)



# ---------------------------
# Edit Profile API
# ---------------------------
class EditProfileAPIView(APIView):
    """
    GET/PUT: Retrieve or update user profile.
    - Handles both Account basic fields and nested UserProfile.
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Retrieve user profile",
        responses={200: AccountSerializer},
        tags=['Accounts'],
    )
    def get(self, request):
        userprofile, _ = UserProfile.objects.get_or_create(user=request.user)
        data = AccountSerializer(request.user).data
        return Response(data)

    @swagger_auto_schema(
        request_body=UserProfileSerializer,
        operation_summary="Update user profile",
    )
    def put(self, request):
        user = request.user
        user_form_data = {
            'first_name': request.data.get('first_name', user.first_name),
            'last_name': request.data.get('last_name', user.last_name),
            'phone_number': request.data.get('phone_number', user.phone_number),
        }
        # Update Account fields
        Account.objects.filter(pk=user.pk).update(**user_form_data)
        # Update UserProfile fields
        user_profile = UserProfile.objects.get_or_create(user=user)[0]
        profile_serializer = UserProfileSerializer(user_profile, data=request.data, partial=True)
        profile_serializer.is_valid(raise_exception=True)
        profile_serializer.save()
        return Response({"detail": "Profile updated."}, status=status.HTTP_200_OK)


# ---------------------------
# Change Password API
# ---------------------------
class ChangePasswordAPIView(APIView):
    """
    POST: Allow authenticated users to change password given current password.
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Change password",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'current_password': openapi.Schema(type=openapi.TYPE_STRING),
                'new_password': openapi.Schema(type=openapi.TYPE_STRING),
                'confirm_password': openapi.Schema(type=openapi.TYPE_STRING),
            }
        ),
        tags=['Accounts'],
    )
    def post(self, request):
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        user = request.user
        if new_password != confirm_password:
            return Response({"error": "New passwords do not match."}, status=status.HTTP_400_BAD_REQUEST)
        if not user.check_password(current_password):
            return Response({"error": "Current password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()
        return Response({"detail": "Password updated successfully."})


# ---------------------------
# My Orders & Order Detail APIs (parity with MVT)
# ---------------------------
class MyOrdersAPIView(APIView):
    """
    GET: Return user's completed orders.
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(operation_summary="List my orders",)
    def get(self, request):
        orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')
        data = []
        for o in orders:
            data.append({
                "order_number": o.order_number,
                "total": getattr(o, "order_total", None),
                "created_at": o.created_at,
            })
        return Response({"orders": data})


class OrderDetailAPIView(APIView):
    """
    GET: details for a single order (order_id = order_number).
    Edge cases:
    - Order not found or not belonging to user => 404/403
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(operation_summary="Order detail",tags=['Accounts'],)
    def get(self, request, order_id):
        order = get_object_or_404(Order, order_number=order_id, user=request.user, is_ordered=True)
        order_items = OrderProduct.objects.filter(order__order_number=order_id)
        subtotal = sum(i.product_price * i.quantity for i in order_items)
        # Minimal serialization to keep parity with MVT view
        items = [
            {"product_name": getattr(p, "product", None) and getattr(p.product, "name", None),
             "quantity": p.quantity,
             "price": p.product_price}
            for p in order_items
        ]
        return Response({
            "order": {
                "order_number": order.order_number,
                "subtotal": subtotal,
                "items": items,
            }
        })


# ---------------------------
# Activation / Password Reset (mirrors original MVT)
# ---------------------------
class ActivateAPIView(APIView):
    """
    GET: Activate user with uidb64 and token (from activation email).
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = Account._default_manager.get(pk=uid)
        except Exception:
            user = None
        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            frontend_url = (
                    f"{settings.FRONTEND_URL}/auth/login"
                    f"?command=verification&email={user.email}"
                )
            return redirect(frontend_url)
        return redirect(f"{settings.FRONTEND_URL}/auth/login?command=invalid")

class ForgotPasswordAPIView(APIView):
    """
    POST: Send reset password email.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        try:
            user = Account.objects.get(email=email)
        except Account.DoesNotExist:
            return Response({"error": "Account does not exist."}, status=status.HTTP_400_BAD_REQUEST)

        # Generate UID and token
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        # Check for test header
        is_api_test = request.headers.get("X-API-Test") == "true"

        current_site = get_current_site(request)
        mail_subject = "Reset Your Password"
        message = render_to_string(
            "accounts/reset_password_email.html",
            {
                "user": user,
                "domain": current_site,
                "uid": uid,
                "token": token,
            },
        )

        # Send the actual email (skip error for demo)
        try:
            EmailMessage(mail_subject, message, to=[email]).send()
        except Exception:
            pass

        # Return UID & token only when testing via Postman
        if is_api_test:
            return Response(
                {
                    "detail": "Password reset email sent (test mode).",
                    "activation_uid": uid,
                    "activation_token": token,
                    "reset_password_active_url": f"/accounts/reset-password-validate/{uid}/{token}/",
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"detail": "Password reset email sent successfully."},
            status=status.HTTP_200_OK,
        )



class ResetPasswordValidateAPIView(APIView):
    """
    Validate password reset token and user identity.
    """

    @swagger_auto_schema(
        operation_summary="Validate Password Reset Token",
        operation_description=(
            "This API verifies whether the password reset link is still valid. "
            "If valid, it returns a success message allowing the user to reset their password."
        ),
        responses={
            200: openapi.Response("Token valid — user can reset password"),
            400: openapi.Response("Invalid or expired link"),
        },
        manual_parameters=[
            openapi.Parameter(
                "uidb64", openapi.IN_PATH, description="Base64 user ID", type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                "token", openapi.IN_PATH, description="Password reset token", type=openapi.TYPE_STRING
            ),
        ],
    )
    def get(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = Account._default_manager.get(pk=uid)
        except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            request.session['uid'] = uid
            return Response(
                {"message": "Token valid. Please reset your password."},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"error": "Invalid or expired link."},
                status=status.HTTP_400_BAD_REQUEST
            )


class ResetPasswordAPIView(APIView):
    """
    Reset password using session-stored UID after token validation.
    """

    @swagger_auto_schema(
        operation_summary="Reset User Password",
        operation_description=(
            "This endpoint resets the user's password after the token validation step. "
            "It requires both `password` and `confirm_password` fields."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['password', 'confirm_password'],
            properties={
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='New password'),
                'confirm_password': openapi.Schema(type=openapi.TYPE_STRING, description='Confirm new password'),
            },
        ),
        responses={
            200: openapi.Response("Password reset successful"),
            400: openapi.Response("Password mismatch or invalid session"),
            404: openapi.Response("User not found"),
        },
    )
    def post(self, request):
        password = request.data.get('password')
        confirm_password = request.data.get('confirm_password')

        if not password or not confirm_password:
            return Response(
                {"error": "Both password fields are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if password != confirm_password:
            return Response(
                {"error": "Passwords do not match."},
                status=status.HTTP_400_BAD_REQUEST
            )

        uid = request.session.get('uid')
        if not uid:
            return Response(
                {"error": "Session expired or invalid. Please retry the password reset link."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            del request.session['uid']
            return Response(
                {"message": "Password reset successful. You can now log in."},
                status=status.HTTP_200_OK
            )
        except Account.DoesNotExist:
            return Response(
                {"error": "User not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        

class DeleteAccountAPIView(APIView):
    """
    POST: Permanently delete user account and associated data.
    - Requires password confirmation for security
    - Handles related profile and order data cleanup
    - Complies with GDPR/data protection standards
    - Uses POST instead of DELETE for better client compatibility
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Permanently delete user account",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['password'],
            properties={
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Current password for confirmation'),
            }
        ),
        responses={
            200: openapi.Response('Account deleted successfully'),
            400: openapi.Response('Invalid password or request'),
        }
    )
    def post(self, request):
        password = request.data.get('password')
        user = request.user
        
        if not password:
            return Response(
                {"error": "Password confirmation required for account deletion."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not user.check_password(password):
            return Response(
                {"error": "Invalid password. Account deletion requires password confirmation."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Store user email for confirmation message
        user_email = user.email
        
        # Perform cascading deletion (UserProfile will be deleted via CASCADE)
        user.delete()
        
        return Response(
            {"detail": f"Account {user_email} has been permanently deleted along with all associated data."},
            status=status.HTTP_200_OK
        )


