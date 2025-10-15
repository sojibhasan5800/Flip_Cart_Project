# orders/api/views.py
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import Payment, Order, OrderProduct
from .serializers import PaymentSerializer, OrderSerializer, OrderProductSerializer
from accounts.models import Account
from carts.models import CartItem
from store.models import Product
from .utils import send_order_to_queue
from django.urls import reverse
import random, string, time

# ---------------------------
# Utility to generate transaction ID
# ---------------------------
def generate_transaction_id():
    timestamp = int(time.time())
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"TXN{timestamp}{random_str}"

# ---------------------------
# Order List/Create API
# ---------------------------
class OrderListCreateAPIView(generics.ListCreateAPIView):
    """
    GET: List all orders (admin only)
    POST: Place a new order
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        with transaction.atomic():
            order = serializer.save(user=user, is_ordered=False)
            order.order_number = f"{time.strftime('%Y%m%d')}{order.id}"
            order.save()
            # Optional: Publish event to RabbitMQ
            payload = {
                "event_type": "order.created",
                "order_id": order.id,
                "order_number": order.order_number,
                "user_id": user.id,
                "total": float(order.order_total),
                "seller_ids": list({user.id for user in Account.objects.filter(email='admin@gmail.com')}),
                "items": [{"product_id": item.product.id, "qty": item.quantity, "price": float(item.product.price)}
                          for item in CartItem.objects.filter(user=user)],
                "created_at": order.created_at.isoformat(),
                "idempotency_key": f"order:{order.order_number}"
            }
            transaction.on_commit(lambda: send_order_to_queue(payload))

# ---------------------------
# Order Detail API
# ---------------------------
class OrderDetailAPIView(generics.RetrieveAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

# ---------------------------
# Payment Success API
# ---------------------------
class PaymentSuccessAPIView(APIView):
    """
    POST: Update payment and mark order as completed
    """
    permission_classes = [permissions.AllowAny]  # Can adjust per auth requirements

    def post(self, request, *args, **kwargs):
        data = request.data
        email = data.get('email')
        transaction_id = data.get('transaction_id')
        status_payment = data.get('status')
        payment_method = data.get('payment_method')
        paid_amount = data.get('paid')
        order_number = data.get('order_number')

        try:
            user = Account.objects.get(email=email)
            order = Order.objects.get(user=user, is_ordered=False, order_number=order_number)
        except (Account.DoesNotExist, Order.DoesNotExist):
            return Response({"error": "User or order not found"}, status=404)

        if status_payment.lower() in ['fail', 'cancel']:
            return Response({"error": "Payment failed or cancelled"}, status=400)

        payment = Payment.objects.create(
            user=user,
            payment_id=transaction_id,
            payment_method=payment_method,
            amount_paid=paid_amount,
            status=status_payment
        )
        order.payment = payment
        order.is_ordered = True
        order.save()

        # Move CartItem to OrderProduct
        cart_items = CartItem.objects.filter(user=user)
        for item in cart_items:
            op = OrderProduct.objects.create(
                order=order,
                payment=payment,
                user=user,
                product=item.product,
                quantity=item.quantity,
                product_price=item.product.price,
                ordered=True
            )
            op.variations.set(item.variations.all())
            item.product.stock -= item.quantity
            item.product.save()
        cart_items.delete()

        return Response({"order_number": order.order_number, "payment_id": payment.payment_id})
