# seller_dashboard/api/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.core.cache import cache
from django.contrib.auth import get_user_model
from .models import SellerAnalytics
from .serializers import SellerAnalyticsSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

User = get_user_model()


class SellerAnalyticsAPIView(APIView):
    """
    GET: Retrieve seller analytics from cache or DB
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Retrieve seller analytics data"
    )
    def get(self, request):
        seller = request.user
        cache_key = f"seller_analytics:{seller.id}"
        data = cache.get(cache_key)
        
        if not data:
            # Fallback to DB with proper error handling
            try:
                analytics = SellerAnalytics.objects.get(seller=seller)
                serializer = SellerAnalyticsSerializer(analytics)
                data = serializer.data
                cache.set(cache_key, data, timeout=300)
            except SellerAnalytics.DoesNotExist:
                # Return empty data structure instead of empty dict
                data = {
                    'total_sales': 0,
                    'total_orders': 0,
                    'total_items_sold': 0,
                    'top_products': {},
                    'inventory_summary': {},
                    'last_updated': None
                }
        
        return Response(data)