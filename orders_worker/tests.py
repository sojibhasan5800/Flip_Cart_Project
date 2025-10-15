# orders_worker/tests/test_worker.py
from django.test import TestCase
from unittest.mock import patch
from orders.models import Order, Payment
from django.contrib.auth import get_user_model
from carts.models import CartItem
from store.models import Product

User = get_user_model()

class RabbitMQWorkerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="test@example.com", password="pass123")
        self.product = Product.objects.create(product_name="Test Product", price=100, stock=10)
        self.order = Order.objects.create(user=self.user, order_total=100)
        CartItem.objects.create(user=self.user, product=self.product, quantity=1)

    @patch("orders_worker.management.commands.run_worker.pika.BlockingConnection")
    def test_process_order_creates_payment(self, mock_connection):
        from orders_worker.management.commands.run_worker import Command
        worker = Command()
        payload = {"event_type": "order.created", "order_id": self.order.id}
        worker.process_order(payload)
        self.order.refresh_from_db()
        self.assertTrue(self.order.is_ordered)
        self.assertTrue(Payment.objects.filter(user=self.user).exists())
