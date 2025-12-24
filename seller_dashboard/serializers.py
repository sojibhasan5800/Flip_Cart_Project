# # seller_dashboard/api/serializers.py
# from rest_framework import serializers
# from .models import SellerAnalytics

# class SellerAnalyticsSerializer(serializers.ModelSerializer):
#     """
#     Serializer for SellerAnalytics model
#     """
#     class Meta:
#         model = SellerAnalytics
#         fields = [
#             'seller',
#             'total_sales',
#             'total_orders',
#             'total_items_sold',
#             'top_products',
#             'inventory_summary',
#             'last_updated'
#         ]
#         read_only_fields = [
#             'total_sales',
#             'total_orders',
#             'total_items_sold',
#             'top_products',
#             'inventory_summary',
#             'last_updated'
#         ]
