# orders/tests/test_orders_api.py
from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from accounts.models import Account
from store.models import Product
from carts.models import CartItem
from .models import Order, OrderProduct

class OrdersAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = Account.objects.create_superuser(email='admin@example.com', username='admin', password='adminpass')
        self.user = Account.objects.create_user(email='user@example.com', username='user', password='userpass')
        self.product = Product.objects.create(product_name='Test Product', price=100, stock=10)
        self.cart_item = CartItem.objects.create(user=self.user, product=self.product, quantity=2)
        self.client.force_authenticate(user=self.user)
        self.list_url = reverse('orders_api:list_create_order')

    def test_place_order(self):
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "phone": "0123456789",
            "email": self.user.email,
            "address_line_1": "Street 1",
            "country": "Bangladesh",
            "state": "Dhaka",
            "city": "Dhaka",
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Order.objects.filter(user=self.user).exists())

    def test_payment_success(self):
        order = Order.objects.create(
            user=self.user, order_number="20231015001", first_name="John", last_name="Doe",
            phone="0123456789", email=self.user.email, address_line_1="Street 1", country="BD",
            state="Dhaka", city="Dhaka", order_total=200, tax=10
        )
        payment_url = reverse('orders_api:payment_success_api')
        data = {
            "email": self.user.email,
            "transaction_id": "TXN123456",
            "status": "success",
            "payment_method": "Stripe",
            "paid": 210,
            "order_number": order.order_number
        }
        response = self.client.post(payment_url, data)
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertTrue(order.is_ordered)
        self.assertIsNotNone(order.payment)
