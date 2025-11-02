from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import Order, OrderProduct, Payment
from carts.models import CartItem,Cart
from store.models import Product
from accounts.models import Account
from .serializers import OrderSerializer, OrderProductSerializer, PaymentSerializer
from .utils import send_order_to_queue
from django.conf import settings
import stripe
import time
import json
import datetime
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.contrib.auth import login
import time, random
from django.urls import reverse
from django.utils.http import urlencode
from sslcommerz_lib import SSLCOMMERZ



# ------------------ Order ViewSet ------------------


class PlaceOrderAPIView(APIView):
    permission_classes = [IsAuthenticated]  # Only logged-in users can access

    """
    GET: Retrieve all orders of the logged-in user with ordered products.
    """
    def get(self, request):
        user = request.user
        orders = Order.objects.filter(user=user).order_by('-created_at')

        if not orders.exists():
            return Response({"detail": "You have no orders yet."}, status=status.HTTP_204_NO_CONTENT)

        order_list = []
        for order in orders:
            order_products = OrderProduct.objects.filter(order=order)
            order_data = {
                "order_number": order.order_number,
                "status": order.status,
                "order_total": order.order_total,
                "tax": order.tax,
                "grand_total": order.order_total,  # Can include discount logic if needed
                "created_at": order.created_at,
                "products": [
                    {
                        "product_id": op.product.id,
                        "product_name": op.product.product_name,
                        "quantity": op.quantity,
                        "price": op.product_price,
                        "variations": [v.variation_category_value for v in op.variations.all()]
                    }
                    for op in order_products
                ]
            }
            order_list.append(order_data)

        return Response(order_list, status=status.HTTP_200_OK)

    """
    POST: Create a new order from the logged-in user's cart.
    """
    def post(self, request):
        user = request.user
        cart_items = CartItem.objects.filter(user=user, is_active=True)

        if not cart_items.exists():
            return Response({"detail": "Your cart is empty."}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate totals
        total = sum([item.product.price * item.quantity for item in cart_items])
        discount = (5 * total) / 100
        grand_total = total - discount

        required_fields = ['first_name', 'last_name', 'phone', 'email', 'address_line_1', 'country', 'state', 'city']
        for field in required_fields:
            if field not in request.data:
                return Response({"detail": f"{field} field is required."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Create Order
            order = Order.objects.create(
                user=user,
                first_name=request.data['first_name'],
                last_name=request.data['last_name'],
                phone=request.data['phone'],
                email=request.data['email'],
                address_line_1=request.data['address_line_1'],
                address_line_2=request.data.get('address_line_2', ''),
                country=request.data['country'],
                state=request.data['state'],
                city=request.data['city'],
                order_note=request.data.get('order_note', ''),
                order_total=grand_total,
                tax=discount,
                ip=request.META.get('REMOTE_ADDR')
            )

            # Generate order number
            today = datetime.date.today()
            order.order_number = f"{today.strftime('%Y%m%d')}{order.id}"
            order.save()

            # Transfer CartItems → OrderProduct
            added_products = []
            for item in cart_items:
                op = OrderProduct.objects.create(
                    order=order,
                    user=user,
                    product=item.product,
                    quantity=item.quantity,
                    product_price=item.product.price,
                    ordered=True
                )
                if item.variations.exists():
                    op.variations.set(item.variations.all())
                op.save()

                added_products.append({
                    "product_id": item.product.id,
                    "product_name": item.product.product_name,
                    "quantity": item.quantity,
                    "price": item.product.price,
                    "variations": [v.variation_category_value for v in item.variations.all()]
                })

            # Clear cart items after ordering
            # cart_items.delete()

        response_data = {
            "order_number": order.order_number,
            "status": order.status,
            "total": total,
            "discount": discount,
            "grand_total": grand_total,
            "products": added_products
        }

        return Response(response_data, status=status.HTTP_201_CREATED)





# ------------------ Order ViewSet ------------------

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by('-created_at')
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        with transaction.atomic():
            order = serializer.save(user=self.request.user)
            # Optional: send to RabbitMQ
            payload = {
                "event_type": "order.created",
                "order_id": order.id,
                "order_number": order.order_number,
                "user_id": order.user.id,
                "total": float(order.order_total),
                "created_at": order.created_at.isoformat(),
                "idempotency_key": f"order:{order.order_number}"
            }
            transaction.on_commit(lambda: send_order_to_queue(payload))

# ------------------ Payment ViewSet ------------------
class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all().order_by('-created_at')
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

# ------------------ OrderProduct ViewSet ------------------
class OrderProductViewSet(viewsets.ModelViewSet):
    queryset = OrderProduct.objects.all().order_by('-created_at')
    serializer_class = OrderProductSerializer
    permission_classes = [IsAuthenticated]



class CreateStripeSessionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        order_id = request.query_params.get('order_id')
        if not order_id:
            return Response({"detail": "order_id query param is required"}, status=400)

        order = get_object_or_404(Order, id=order_id, user=request.user)
        cart_items = CartItem.objects.filter(user=request.user, is_active=True)

        if not cart_items.exists():
            return Response({"detail": "No items in cart"}, status=400)

        line_items = []
        for item in cart_items:
            line_items.append({
                'price_data': {
                    'currency': 'usd',  # BD are bdt
                    'product_data': {'name': item.product.product_name},
                    'unit_amount': int(item.product.price * 100)
                },
                'quantity': item.quantity
            })

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            customer_email=request.user.email,
            success_url=request.build_absolute_uri('/api/orders/stripe/success/') + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.build_absolute_uri('/api/orders/stripe/cancel/'),
            metadata={'order_id': order.id, 'order_number': order.order_number}
        )

        return Response({"checkout_url": session.url})


    

# ------------------ Stripe Webhook ------------------

class StripeWebhookAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        endpoint_secret = settings.STRIPE_ENDPOINT_SECRET
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        except Exception:
            return Response(status=400)

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            order_id = session['metadata']['order_id']
            order_number = session['metadata']['order_number']
            try:
                order = Order.objects.get(id=order_id, order_number=order_number)
                payload = {
                    "event_type":"order.created",
                    "order_id": order.id,
                    "order_number": order.order_number,
                    "user_id": order.user.id,
                    "total": float(order.order_total),
                    "created_at": order.created_at.isoformat(),
                    "idempotency_key": f"order:{order.order_number}"
                }
                transaction.on_commit(lambda: send_order_to_queue(payload))
            except Order.DoesNotExist:
                return Response(status=404)

        return Response(status=200)
    









# ------------------ Stripe Success / Cancel ------------------
from rest_framework import status

class StripeSuccessAPIView(APIView):
    """
    Handle successful Stripe payments.
    Stripe redirects here after checkout completion.
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        session_id = request.GET.get('session_id')
        if not session_id:
            return Response(
                {"error": "Session ID is missing."},
                status=status.HTTP_400_BAD_REQUEST
            )

        stripe.api_key = settings.STRIPE_SECRET_KEY

        try:
            session = stripe.checkout.Session.retrieve(session_id)
        except stripe.error.InvalidRequestError:
            return Response(
                {"error": "Invalid or expired session ID."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"Something went wrong: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        payment_status = session.get('payment_status', 'unknown')
        customer_email = session.get('customer_email')
        amount_total = session.get('amount_total', 0) / 100 

        data = {
            "message": " Payment successful",
            "payment_status": payment_status,
            "customer_email": customer_email,
            "amount_paid": amount_total,
            "currency": session.get('currency', 'usd'),
            "session_id": session.id,
            "redirect_from": "Stripe",
        }

        return Response(data, status=status.HTTP_200_OK)



class StripeCancelAPIView(APIView):
    """
    Handle canceled or failed Stripe payments.
    Stripe redirects here if the user cancels payment.
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        data = {
            "message": " Payment canceled by user.",
            "status": "canceled",
            "redirect_from": "Stripe"
        }
        return Response(data, status=status.HTTP_200_OK)
    


def generate_transaction_id():
    timestamp = int(time.time())
    random_str = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=6))
    return f"TXN{timestamp}{random_str}"




class SSLPaymentAPIView(APIView):
    """
    Generate SSLCommerz payment session and return Gateway URL
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        order_id = request.data.get("order_id")
        amount = request.data.get("amount")  # Total amount to pay

        if not order_id or not amount:
            return Response({"detail": "Missing order_id or amount"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            order = Order.objects.get(id=order_id, user=user, is_ordered=False)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found or already paid"}, status=status.HTTP_404_NOT_FOUND)

        # Validate stock
        cart_items = CartItem.objects.filter(user=user)
        for item in cart_items:
            product = Product.objects.get(id=item.product.id)
            if product.stock < item.quantity:
                return Response({
                    "detail": f" Not enough stock for '{product.product_name}' (Available: {product.stock})"
                }, status=status.HTTP_400_BAD_REQUEST)

        # Generate unique transaction ID
        trans_id = generate_transaction_id()

        # Build success, fail, cancel URLs
        base_url = f"{request.scheme}://{request.get_host()}"
        query_params = {
            "email": user.email,
            "transction_id": trans_id,
            "payment_method": "SSLCommerz",
            "paid": amount,
            "order_number": order.order_number
        }
        query_string = urlencode(query_params)
        success_url = f"{base_url}{reverse('payment_success')}?{query_string}"
        fail_url = f"{base_url}{reverse('payment_fail')}?{query_string}"
        cancel_url = f"{base_url}{reverse('payment_cancel')}?{query_string}"

        # SSLCommerz configuration
        ssl_settings = {
            "store_id": "trans68369e6df24cb",
            "store_pass": "trans68369e6df24cb@ssl",
            "issandbox": True
        }
        sslcz = SSLCOMMERZ(ssl_settings)

        # Payment details
        post_body = {
            "total_amount": amount,
            "currency": "BDT",
            "tran_id": trans_id,
            "success_url": success_url,
            "fail_url": fail_url,
            "cancel_url": cancel_url,
            "emi_option": 0,
            "cus_name": user.full_name,
            "cus_email": user.email,
            "cus_phone": user.phone_number,
            "cus_add1": order.address_line_1,
            "cus_city": order.city,
            "cus_country": order.country,
            "shipping_method": "NO",
            "num_of_item": cart_items.count(),
            "product_name": " / ".join([item.product.product_name for item in cart_items]),
            "product_category": " / ".join([item.product.category for item in cart_items]) if hasattr(item.product, 'category') else "General",
            "product_profile": "general"
        }

        # Create session
        response = sslcz.createSession(post_body)

        if response.get("status") == "SUCCESS" and "GatewayPageURL" in response:
            return Response({
                "message": "SSLCommerz session created",
                "gateway_url": response["GatewayPageURL"],
                "transaction_id": trans_id
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "detail": "Failed to create SSLCommerz session",
                "error": response
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        



# -------------------- PAYMENT SUCCESS SSL--------------------

class PaymentSuccessAPIView(APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        email = request.query_params.get('email')
        trans_id = request.query_params.get('transction_id')
        payment_method = request.query_params.get('payment_method')
        paid = request.query_params.get('paid')
        status_code = request.query_params.get('status')
        order_number = request.query_params.get('order_number')

        if not email or not order_number:
            return Response({"detail": "Missing required parameters"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            current_user = Account.objects.get(email=email)
            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
        except (Account.DoesNotExist, Order.DoesNotExist):
            return Response({"detail": "Invalid user or order"}, status=status.HTTP_404_NOT_FOUND)

        # Check stock first
        cart_items = CartItem.objects.filter(user=current_user)
        for item in cart_items:
            product = Product.objects.select_for_update().get(id=item.product_id)
            if product.stock < item.quantity:
                raise Exception(f" Not enough stock for product '{product.product_name}' (Available: {product.stock})")

        # Save payment info
        payment = Payment.objects.create(
            user=current_user,
            payment_id=trans_id,
            payment_method=payment_method,
            amount_paid=paid,
            status=status_code
        )

        # Update order
        order.payment = payment
        order.is_ordered = True
        order.status = "Completed"
        order.save()

        # Move cart → OrderProduct
        for item in cart_items:
            op = OrderProduct.objects.create(
                order=order,
                payment=payment,
                user=current_user,
                product=item.product,
                quantity=item.quantity,
                product_price=item.product.price,
                ordered=True
            )
            op.variations.set(item.variations.all())
            op.save()

            # Decrease stock
            product = Product.objects.select_for_update().get(id=item.product.id)
            product.stock -= item.quantity
            product.save()

        cart_items.delete()

        # Send confirmation email
        mail_subject = 'Thank you for your order!'
        message = render_to_string('orders/order_recieved_email.html', {'user': current_user, 'order': order})
        EmailMessage(mail_subject, message, to=[current_user.email]).send()

        login(request, current_user)

        return Response({
            "message": " Payment successful and order completed.",
            "order_number": order.order_number,
            "transaction_id": payment.payment_id,
            "status": order.status,
        }, status=status.HTTP_200_OK)


# -------------------- PAYMENT CANCEL --------------------
class PaymentCancelAPIView(APIView):
    """
    When user cancels the SSLCommerz payment manually
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        email = request.query_params.get('email')
        order_number = request.query_params.get('order_number')

        if not email or not order_number:
            return Response({"detail": "Missing parameters"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Account.objects.get(email=email)
            order = Order.objects.get(user=user, order_number=order_number, is_ordered=False)
            order.status = "Cancelled"
            order.save()
        except (Account.DoesNotExist, Order.DoesNotExist):
            return Response({"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "message": " Payment was cancelled by user.",
            "order_number": order_number,
            "status": order.status
        }, status=status.HTTP_200_OK)


# -------------------- PAYMENT FAIL --------------------
class PaymentFailAPIView(APIView):
    """
    When SSLCommerz payment fails (e.g., insufficient balance)
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        email = request.query_params.get('email')
        order_number = request.query_params.get('order_number')

        if not email or not order_number:
            return Response({"detail": "Missing parameters"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Account.objects.get(email=email)
            order = Order.objects.get(user=user, order_number=order_number, is_ordered=False)
            order.status = "Failed"
            order.save()
        except (Account.DoesNotExist, Order.DoesNotExist):
            return Response({"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "message": " Payment failed! Please try again.",
            "order_number": order_number,
            "status": order.status
        }, status=status.HTTP_400_BAD_REQUEST)

