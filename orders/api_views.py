from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import Order, OrderProduct, Payment
from .serializers import OrderSerializer, OrderProductSerializer, PaymentSerializer
from .utils import send_order_to_queue
from django.conf import settings
import stripe
import time
import json

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
class StripeSuccessAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        session_id = request.GET.get('session_id')
        if not session_id:
            return Response({"detail": "Session ID missing"}, status=400)
        stripe.api_key = settings.STRIPE_SECRET_KEY
        session = stripe.checkout.Session.retrieve(session_id)
        return Response({"message": "Payment successful", "session": session})

class StripeCancelAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        return Response({"message": "Payment canceled"})
