# store/tests/test_api.py
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from store.models import Product, ProductGallery, Variation, ReviewRating
from accounts.models import Account
from category.models import Category
import json
from django_redis import get_redis_connection

class StoreAPITestCase(APITestCase):

    def setUp(self):
        # Create a test category
        self.category = Category.objects.create(name="Test Category", slug="test-category")

        # Create admin user
        self.admin_user = Account.objects.create_superuser(
            email="admin@test.com", password="admin123", first_name="Admin", last_name="User"
        )

        # Create regular user
        self.user = Account.objects.create_user(
            email="user@test.com", password="user123", first_name="Regular", last_name="User"
        )

        # Create test product
        self.product = Product.objects.create(
            product_name="Test Product",
            slug="test-product",
            description="This is a test product",
            price=100,
            stock=10,
            category=self.category
        )

        # Create product gallery
        self.gallery = ProductGallery.objects.create(
            product=self.product,
        )

        # Create a variation
        self.variation = Variation.objects.create(
            product=self.product,
            variation_category='color',
            variation_value='Red',
            is_active=True
        )

        # API clients
        self.client = APIClient()
        self.admin_client = APIClient()
        self.admin_client.force_authenticate(user=self.admin_user)
        self.user_client = APIClient()
        self.user_client.force_authenticate(user=self.user)

    # ------------------ Product Tests ------------------
    def test_product_list_authenticated_user(self):
        url = reverse('store_api:product-list')
        self.user_client.force_authenticate(user=self.user)
        response = self.user_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Test Product', str(response.data))

    def test_product_create_admin_only(self):
        url = reverse('store_api:product-list')
        data = {
            "product_name": "New Product",
            "slug": "new-product",
            "description": "New product description",
            "price": 200,
            "stock": 5,
            "category": self.category.id
        }
        # Regular user should fail
        response = self.user_client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # Admin should succeed
        response = self.admin_client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_product_retrieve_authenticated(self):
        url = reverse('store_api:product-detail', args=[self.product.id])
        response = self.user_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['product_name'], self.product.product_name)

    def test_product_update_delete_admin_only(self):
        url = reverse('store_api:product-detail', args=[self.product.id])
        data = {"price": 150}
        # Regular user cannot update
        response = self.user_client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # Admin can update
        response = self.admin_client.put(url, {
            "product_name": self.product.product_name,
            "slug": self.product.slug,
            "description": self.product.description,
            "price": 150,
            "stock": self.product.stock,
            "category": self.category.id
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.price, 150)

    # ------------------ Review Tests ------------------
    def test_create_review_and_redis_cache(self):
        url = reverse('store_api:review-create')
        data = {"product": self.product.id, "subject": "Great", "review": "Awesome product", "rating": 5.0}
        response = self.user_client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Redis cache check
        cache = get_redis_connection("default")
        cached_data = cache.get(f'product_reviews:{self.product.id}')
        self.assertIsNotNone(cached_data)
        cached_reviews = json.loads(cached_data)
        self.assertEqual(len(cached_reviews), 1)
        self.assertEqual(cached_reviews[0]['subject'], "Great")

    # ------------------ ProductGallery Tests ------------------
    def test_gallery_list_authenticated_user(self):
        url = reverse('store_api:gallery-list')
        response = self.user_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_gallery_create_admin_only(self):
        url = reverse('store_api:gallery-list')
        response = self.user_client.post(url, {"product": self.product.id})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.admin_client.post(url, {"product": self.product.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # ------------------ Variation Tests ------------------
    def test_variation_list_authenticated_user(self):
        url = reverse('store_api:variation-list')
        response = self.user_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_variation_create_admin_only(self):
        url = reverse('store_api:variation-list')
        data = {"product": self.product.id, "variation_category": "size", "variation_value": "M", "is_active": True}
        response = self.user_client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.admin_client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

