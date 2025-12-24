from django.test import TestCase

# Create your tests here.
# category/tests/test_category_api.py
from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from ..models import Category
from django.contrib.auth import get_user_model

User = get_user_model()

class CategoryAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser(
            email='admin@example.com', username='admin', password='adminpass'
        )
        self.client.force_authenticate(user=self.admin_user)
        self.load_url = reverse('category_api:load_category')
        self.list_url = reverse('category_api:list_create_category')
        self.category = Category.objects.create(category_name='Electronics', slug='electronics')

    def test_load_category_api(self):
        resp = self.client.get(self.load_url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('loaded_categories', resp.data)

    def test_category_list(self):
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), Category.objects.count())

    def test_create_category(self):
        resp = self.client.post(self.list_url, {'category_name': 'Books', 'slug': 'books'})
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(Category.objects.filter(slug='books').exists())

    def test_category_detail_get(self):
        url = reverse('category_api:detail_category', args=[self.category.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['slug'], 'electronics')

    def test_category_update(self):
        url = reverse('category_api:detail_category', args=[self.category.id])
        resp = self.client.put(url, {'category_name': 'Electro', 'slug': 'electro'})
        self.assertEqual(resp.status_code, 200)
        self.category.refresh_from_db()
        self.assertEqual(self.category.slug, 'electro')

    def test_category_delete(self):
        url = reverse('category_api:detail_category', args=[self.category.id])
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(Category.objects.filter(id=self.category.id).exists())
