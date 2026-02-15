# # seller_dashboard/tests/test_api.py
# from django.test import TestCase
# from rest_framework.test import APIClient
# from django.urls import reverse
# from django.contrib.auth import get_user_model
# from .models import SellerAnalytics

# User = get_user_model()

# class SellerDashboardAPITestCase(TestCase):
#     def setUp(self):
#         self.client = APIClient()
#         self.seller = User.objects.create_user(email='seller@example.com', password='sellerpass')
#         self.analytics = SellerAnalytics.objects.create(
#             seller=self.seller,
#             total_sales=1000,
#             total_orders=5,
#             total_items_sold=10,
#             top_products={"Product1": 5},
#             inventory_summary={"1": {"name": "Product1", "stock": 20}}
#         )
#         self.client.force_authenticate(user=self.seller)
#         self.api_url = reverse('seller_dashboard_api:analytics')

#     def test_get_seller_analytics(self):
#         resp = self.client.get(self.api_url)
#         self.assertEqual(resp.status_code, 200)
#         self.assertEqual(resp.data['total_sales'], 1000)
#         self.assertIn('top_products', resp.data)
#         self.assertIn('inventory_summary', resp.data)
