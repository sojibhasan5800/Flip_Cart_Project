# carts/tests/test_cart_api.py
from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from store.models import Product
from accounts.models import Account
from .models import Cart, CartItem

class CartAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = Account.objects.create_user(email='user@example.com', password='userpass', username='user')
        self.product = Product.objects.create(name='Test Product', price=100)
        self.client.force_authenticate(user=self.user)
        self.list_url = reverse('carts_api:cart_items')

    def test_add_to_cart(self):
        resp = self.client.post(self.list_url, {'product_id': self.product.id, 'quantity': 2})
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(CartItem.objects.filter(user=self.user).count(), 1)

    def test_get_cart_items(self):
        CartItem.objects.create(product=self.product, quantity=1, user=self.user)
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)

    def test_update_cart_item_quantity(self):
        cart_item = CartItem.objects.create(product=self.product, quantity=1, user=self.user)
        url = reverse('carts_api:cart_item_detail', args=[cart_item.id])
        resp = self.client.put(url, {'quantity': 5})
        self.assertEqual(resp.status_code, 200)
        cart_item.refresh_from_db()
        self.assertEqual(cart_item.quantity, 5)

    def test_delete_cart_item(self):
        cart_item = CartItem.objects.create(product=self.product, quantity=1, user=self.user)
        url = reverse('carts_api:cart_item_detail', args=[cart_item.id])
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(CartItem.objects.filter(id=cart_item.id).exists())
