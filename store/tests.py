# store/tests/test_store_api.py
from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from .models import Product, Category, ReviewRating
from django.contrib.auth import get_user_model

User = get_user_model()

class StoreAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser(email='admin@example.com', username='admin', password='adminpass')
        self.client.force_authenticate(user=self.admin_user)
        
        self.category = Category.objects.create(category_name='Electronics', slug='electronics')
        self.product = Product.objects.create(product_name='Laptop', slug='laptop', price=50000, stock=5, category=self.category)

        self.product_list_url = reverse('store_api:product-list')
        self.product_detail_url = reverse('store_api:product-detail', args=[self.product.id])

    def test_product_list(self):
        resp = self.client.get(self.product_list_url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data[0]['product_name'], 'Laptop')

    def test_product_detail(self):
        resp = self.client.get(self.product_detail_url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['slug'], 'laptop')
