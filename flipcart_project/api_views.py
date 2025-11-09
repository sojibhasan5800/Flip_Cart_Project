# home/api_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import CursorPagination
from store.models import Product
from store.serializers import ProductSerializer
from django_redis import get_redis_connection
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import json


class HomeProductCursorPagination(CursorPagination):
    page_size = 12
    ordering = '-created_date'  # Show newest products first
    cursor_query_param = 'cursor'


class HomeProductsAPIView(APIView):
    """
    Homepage Product API with Infinite Scroll (Initial Data Load)
    """

    @swagger_auto_schema(
        operation_summary="Fetch initial homepage products (with caching)",
        operation_description=(
            "Fetch the first batch of available products for the homepage with cursor pagination. "
            "If Redis cache is available, data will be fetched from cache to improve performance."
        ),
        responses={
            200: openapi.Response(
                description="Products fetched successfully",
                examples={
                    "application/json": {
                        "status": True,
                        "message": "Initial products fetched successfully",
                        "data": {
                            "products": [
                                {
                                    "id": 1,
                                    "product_name": "iPhone 15",
                                    "price": "999.99",
                                    "image_url": "https://example.com/product1.jpg",
                                }
                            ],
                            "has_next": True,
                            "next_cursor": 3,
                            "total_initial_products": 12,
                        },
                    }
                },
            ),
            404: openapi.Response(
                description="No products available",
                examples={"application/json": {"status": False, "message": "No products available", "data": []}},
            ),
        },
        tags=["Home Products"],
    )
        
    
    def get(self, request):
        # Try to fetch cached data from Redis
        cache_key = 'home_products'
        cache = get_redis_connection("default")

        # Check if cached data exists
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response({
                'status': True,
                'message': 'Products fetched from cache',
                'data': json.loads(cached_data)
            })

        # If cache not found, fetch data from database
        products = Product.objects.filter(is_available=True).order_by('-created_date')[:12]

        if not products.exists():
            return Response({
                'status': False,
                'message': 'No products available',
                'data': []
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = ProductSerializer(products, many=True)

        # Prepare response data
        response_data = {
            'products': serializer.data,
            'has_next': products.count() == 12,  # If 12 products exist, more are available
            'next_cursor': products.last().id if products else None,
            'total_initial_products': products.count(),
        }

        # Cache data in Redis (1 hour)
        cache.set(cache_key, json.dumps(response_data), ex=3600)

        return Response({
            'status': True,
            'message': 'Initial products fetched successfully',
            'data': response_data
        })


class LoadMoreProductsAPIView(APIView):
    """
    Load More Products API for Infinite Scroll
    """

    @swagger_auto_schema(
        operation_summary="Load more products for infinite scrolling",
        operation_description=(
            "Fetch next batch of products based on the cursor (last product ID from the previous response). "
            "Useful for infinite scroll or pagination systems."
        ),
        manual_parameters=[
            openapi.Parameter(
                'cursor',
                openapi.IN_QUERY,
                description="ID of the last loaded product (used for pagination)",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
        ],
        responses={
            200: openapi.Response(
                description="More products loaded successfully",
                examples={
                    "application/json": {
                        "status": True,
                        "message": "More products loaded successfully",
                        "data": {
                            "products": [
                                {
                                    "id": 2,
                                    "product_name": "MacBook Air",
                                    "price": "1299.99",
                                    "image_url": "https://example.com/product2.jpg",
                                }
                            ],
                            "has_next": False,
                            "next_cursor": None,
                            "count": 2,
                        },
                    }
                },
            ),
            400: openapi.Response(
                description="Invalid cursor parameter",
                examples={
                    "application/json": {
                        "status": False,
                        "message": "Cursor parameter is required",
                        "data": [],
                    }
                },
            ),
            500: openapi.Response(
                description="Server error",
                examples={
                    "application/json": {
                        "status": False,
                        "message": "Error loading products: internal error",
                        "data": [],
                    }
                },
            ),
        },
        tags=["Home Products"],
    )
    
    
    def get(self, request):
        cursor = request.GET.get('cursor')

        if not cursor:
            return Response({
                'status': False,
                'message': 'Cursor parameter is required',
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            cursor_id = int(cursor)
            page_size = 12

            # Cursor-based pagination
            products = Product.objects.filter(
                is_available=True,
                id__lt=cursor_id  # Get products with IDs smaller than cursor_id
            ).order_by('-created_date')[:page_size]

            serializer = ProductSerializer(products, many=True)

            next_cursor = products.last().id if products else None
            has_next = Product.objects.filter(
                is_available=True,
                id__lt=next_cursor
            ).exists() if next_cursor else False

            response_data = {
                'products': serializer.data,
                'has_next': has_next,
                'next_cursor': next_cursor,
                'count': len(serializer.data)
            }

            return Response({
                'status': True,
                'message': 'More products loaded successfully',
                'data': response_data
            })

        except ValueError:
            return Response({
                'status': False,
                'message': 'Invalid cursor format',
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'status': False,
                'message': f'Error loading products: {str(e)}',
                'data': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
