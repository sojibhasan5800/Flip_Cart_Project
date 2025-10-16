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

from .models import Account, UserProfile
from .serializers import (
    RegistrationSerializer, LoginSerializer, AccountSerializer, UserProfileSerializer
)
from orders.models import Order, OrderProduct  # keep parity with your views (requires orders app)

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
        operation_description="Creates a new user account and sends activation email.",
        responses={201: openapi.Response('User created', AccountSerializer)}
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Activation email (use same template as earlier)
        current_site = get_current_site(request)
        mail_subject = 'Please activate your account'
        message = render_to_string('accounts/account_verification_email.html', {
            'user': user,
            'domain': current_site,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': default_token_generator.make_token(user),
            'api':True,
        })
        to_email = user.email
        try:
            EmailMessage(mail_subject, message, to=[to_email]).send()
        except Exception:
            # Non-fatal: still return created but log/notify in production
            pass
        return Response({"detail": "User created. Check email for activation link."}, status=status.HTTP_201_CREATED)


# ---------------------------
# Login API
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
        responses={200: 'token'}
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        # Generate JWT tokens
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

    @swagger_auto_schema(operation_summary="Logout user")
    def post(self, request):
        try:
        # blacklist all refresh tokens for user
            tokens = OutstandingToken.objects.filter(user=request.user)
            for token in tokens:
                BlacklistedToken.objects.get_or_create(token=token)
        except Exception:
            pass
        return Response({"detail": "Logged out."}, status=status.HTTP_200_OK)


# ---------------------------
# Dashboard API
# ---------------------------
class DashboardAPIView(APIView):
    """
    GET: Returns basic dashboard info for authenticated user.
    - Counts user's completed orders and returns basic profile data.
    Performance:
    - Limit DB hits; uses `count()` instead of retrieving objects fully where possible.
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(operation_summary="User dashboard")
    def get(self, request):
        orders_qs = Order.objects.filter(user_id=request.user.id, is_ordered=True).order_by('-created_at')
        orders_count = orders_qs.count()
        userprofile, _ = UserProfile.objects.get_or_create(user=request.user)
        data = {
            "orders_count": orders_count,
            "user": AccountSerializer(request.user).data,
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
        responses={200: AccountSerializer}
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
        )
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

    @swagger_auto_schema(operation_summary="List my orders")
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

    @swagger_auto_schema(operation_summary="Order detail")
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
            return Response({"detail": "Account activated."})
        return Response({"error": "Invalid activation link."}, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordAPIView(APIView):
    """
    POST: Send reset password email.
    """
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(operation_summary="Request password reset", request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={'email': openapi.Schema(type=openapi.TYPE_STRING)}
    ))
    def post(self, request):
        email = request.data.get('email')
        try:
            user = Account.objects.get(email=email)
        except Account.DoesNotExist:
            return Response({"error": "Account does not exist."}, status=status.HTTP_400_BAD_REQUEST)
        current_site = get_current_site(request)
        mail_subject = 'Reset Your Password'
        message = render_to_string('accounts/reset_password_email.html', {
            'user': user,
            'domain': current_site,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': default_token_generator.make_token(user),
        })
        try:
            EmailMessage(mail_subject, message, to=[email]).send()
        except Exception:
            pass
        return Response({"detail": "Password reset email sent."})


class ResetPasswordAPIView(APIView):
    """
    POST: Set new password after validating session uid stored by validate endpoint.
    (Alternatively accept uid + token here for stateless flow.)
    """
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(operation_summary="Reset password", request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={'uid': openapi.Schema(type=openapi.TYPE_STRING),
                    'token': openapi.Schema(type=openapi.TYPE_STRING),
                    'password': openapi.Schema(type=openapi.TYPE_STRING),
                    'confirm_password': openapi.Schema(type=openapi.TYPE_STRING)}
    ))
    def post(self, request):
        uid = request.data.get('uid')
        token = request.data.get('token')
        password = request.data.get('password')
        confirm_password = request.data.get('confirm_password')
        if not all([uid, token, password, confirm_password]):
            return Response({"error": "All fields required."}, status=status.HTTP_400_BAD_REQUEST)
        if password != confirm_password:
            return Response({"error": "Passwords do not match."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            uid_decoded = urlsafe_base64_decode(uid).decode()
            user = Account._default_manager.get(pk=uid_decoded)
        except Exception:
            return Response({"error": "Invalid uid."}, status=status.HTTP_400_BAD_REQUEST)
        if not default_token_generator.check_token(user, token):
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(password)
        user.save()
        return Response({"detail": "Password reset successful."})
