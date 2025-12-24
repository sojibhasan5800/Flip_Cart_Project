# # home/api_views.py
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from rest_framework.pagination import CursorPagination
# from store.models import Product
# from store.serializers import ProductSerializer
# from django_redis import get_redis_connection
# from drf_yasg.utils import swagger_auto_schema
# from drf_yasg import openapi
# import json
# from django_tenants.utils import schema_context
# # from delivery_system.models import DeliveryTenant





# class HomeProductCursorPagination(CursorPagination):
#     page_size = 12
#     ordering = '-created_date'  # Show newest products first
#     cursor_query_param = 'cursor'


# class HomeProductsAPIView(APIView):
#     """
#     Homepage Product API with Infinite Scroll (Initial Data Load)
#     """

#     @swagger_auto_schema(
#         operation_summary="Fetch initial homepage products (with caching)",
#         operation_description=(
#             "Fetch the first batch of available products for the homepage with cursor pagination. "
#             "If Redis cache is available, data will be fetched from cache to improve performance."
#         ),
#         responses={
#             200: openapi.Response(
#                 description="Products fetched successfully",
#                 examples={
#                     "application/json": {
#                         "status": True,
#                         "message": "Initial products fetched successfully",
#                         "data": {
#                             "products": [
#                                 {
#                                     "id": 1,
#                                     "product_name": "iPhone 15",
#                                     "price": "999.99",
#                                     "image_url": "https://example.com/product1.jpg",
#                                 }
#                             ],
#                             "has_next": True,
#                             "next_cursor": 3,
#                             "total_initial_products": 12,
#                         },
#                     }
#                 },
#             ),
#             404: openapi.Response(
#                 description="No products available",
#                 examples={"application/json": {"status": False, "message": "No products available", "data": []}},
#             ),
#         },
#         tags=["Home Products"],
#     )
        
    
#     def get(self, request):
#         # Try to fetch cached data from Redis
#         all_products = []
#         cache_key = 'home_products'
#         cache = get_redis_connection("default")

#         # Check if cached data exists
#         cached_data = cache.get(cache_key)
#         if cached_data:
#             return Response({
#                 'status': True,
#                 'message': 'Products fetched from cache',
#                 'data': json.loads(cached_data)
#             })

#         # Fetch products from all active tenants
#         tenants = DeliveryTenant.objects.filter(is_active=True)
#         for tenant in tenants:

#             # Switch to tenant schema
#             with schema_context(tenant.schema_name):
#                 products = Product.objects.filter(is_available=True).order_by('-created_date')[:12]
#                 serializer = ProductSerializer(products, many=True)

#                 # Add store info for each product
#                 for product_data in serializer.data:
#                     product_data['store_name'] = tenant.name
#                     product_data['store_domain'] = tenant.domains.first().domain if tenant.domains.exists() else None
#                     all_products.append(product_data)

#             if not all_products:
#                 return Response({
#                     'status': False,
#                     'message': 'No products available',
#                     'data': []
#                 }, status=status.HTTP_404_NOT_FOUND)

       

#         if not products.exists():
#             return Response({
#                 'status': False,
#                 'message': 'No products available',
#                 'data': []
#             }, status=status.HTTP_404_NOT_FOUND)

#         serializer = ProductSerializer(products, many=True)

#        # Prepare response data
#         response_data = {
#             'products': all_products,
#             'has_next': len(all_products) == 12,
#             'next_cursor': all_products[-1]['id'] if all_products else None,
#             'total_initial_products': len(all_products),
#         }

#         # Cache the response for 1 hour
#         cache.set(cache_key, json.dumps(response_data), ex=3600)


#         return Response({
#             'status': True,
#             'message': 'Initial products fetched successfully',
#             'data': response_data
#         })


# # home/api_views.py

# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from rest_framework.pagination import CursorPagination
# from store.models import Product
# from store.serializers import ProductSerializer
# from django_redis import get_redis_connection
# from drf_yasg.utils import swagger_auto_schema
# from drf_yasg import openapi
# import json
# from django_tenants.utils import schema_context
# # from delivery_system.models import DeliveryTenant

# # ---------------------------
# # Cursor Pagination for Home Products
# # ---------------------------
# class HomeProductCursorPagination(CursorPagination):
#     """
#     Cursor-based pagination settings for homepage products
#     """
#     page_size = 12  # number of products per page
#     ordering = '-created_date'  # newest products first
#     cursor_query_param = 'cursor'  # query parameter for pagination

# # ---------------------------
# # HomeProducts API - Initial Data Load
# # ---------------------------
# class HomeProductsAPIView(APIView):
#     """
#     Homepage Product API with Infinite Scroll (Initial Data Load)
#     """
#     @swagger_auto_schema(
#         operation_summary="Fetch initial homepage products (with caching)",
#         operation_description=(
#             "Fetch the first batch of available products for the homepage with cursor pagination. "
#             "If Redis cache is available, data will be fetched from cache to improve performance."
#         ),
#         responses={
#             200: openapi.Response(
#                 description="Products fetched successfully",
#                 examples={
#                     "application/json": {
#                         "status": True,
#                         "message": "Initial products fetched successfully",
#                         "data": {
#                             "products": [
#                                 {
#                                     "id": 1,
#                                     "product_name": "iPhone 15",
#                                     "price": "999.99",
#                                     "image_url": "https://example.com/product1.jpg",
#                                 }
#                             ],
#                             "has_next": True,
#                             "next_cursor": 3,
#                             "total_initial_products": 12,
#                         },
#                     }
#                 },
#             ),
#             404: openapi.Response(
#                 description="No products available",
#                 examples={"application/json": {"status": False, "message": "No products available", "data": []}},
#             ),
#         },
#         tags=["Home Products"],
#     )
    
#     def get(self, request):
#         """
#         Fetch initial homepage products with tenant-aware schema and caching
#         """
#         all_products = []
#         cache_key = 'home_products'
#         cache = get_redis_connection("default")

#         # Try fetching data from Redis cache
#         cached_data = cache.get(cache_key)
#         if cached_data:
#             return Response({
#                 'status': True,
#                 'message': 'Products fetched from cache',
#                 'data': json.loads(cached_data)
#             })

#         # Fetch products from all active tenants
#         tenants = DeliveryTenant.objects.filter(is_active=True)

#         for tenant in tenants:
#             # Switch to tenant schema
#             with schema_context(tenant.schema_name):
#                 products = Product.objects.filter(is_available=True).order_by('-created_date')[:12]
#                 serializer = ProductSerializer(products, many=True)

#                 # Add store info for each product
#                 for product_data in serializer.data:
#                     product_data['store_name'] = tenant.name
#                     product_data['store_domain'] = tenant.domains.first().domain if tenant.domains.exists() else None
#                     all_products.append(product_data)

#         if not all_products:
#             return Response({
#                 'status': False,
#                 'message': 'No products available',
#                 'data': []
#             }, status=status.HTTP_404_NOT_FOUND)

#         # Prepare response data
#         response_data = {
#             'products': all_products,
#             'has_next': len(all_products) == 12,
#             'next_cursor': all_products[-1]['id'] if all_products else None,
#             'total_initial_products': len(all_products),
#         }

#         # Cache the response for 1 hour
#         cache.set(cache_key, json.dumps(response_data), ex=3600)

#         return Response({
#             'status': True,
#             'message': 'Initial products fetched successfully',
#             'data': response_data
#         })


# # ---------------------------
# # LoadMoreProducts API - Infinite Scroll
# # ---------------------------
# class LoadMoreProductsAPIView(APIView):
#     """
#     Load More Products API for Infinite Scroll
#     """
#     @swagger_auto_schema(
#         operation_summary="Load more products for infinite scrolling",
#         operation_description=(
#             "Fetch next batch of products based on the cursor (last product ID from the previous response). "
#             "Useful for infinite scroll or pagination systems."
#         ),
#         manual_parameters=[
#             openapi.Parameter(
#                 'cursor',
#                 openapi.IN_QUERY,
#                 description="ID of the last loaded product (used for pagination)",
#                 type=openapi.TYPE_INTEGER,
#                 required=True,
#             ),
#         ],
#         responses={
#             200: openapi.Response(
#                 description="More products loaded successfully",
#                 examples={
#                     "application/json": {
#                         "status": True,
#                         "message": "More products loaded successfully",
#                         "data": {
#                             "products": [
#                                 {
#                                     "id": 2,
#                                     "product_name": "MacBook Air",
#                                     "price": "1299.99",
#                                     "image_url": "https://example.com/product2.jpg",
#                                 }
#                             ],
#                             "has_next": False,
#                             "next_cursor": None,
#                             "count": 2,
#                         },
#                     }
#                 },
#             ),
#             400: openapi.Response(
#                 description="Invalid cursor parameter",
#                 examples={
#                     "application/json": {
#                         "status": False,
#                         "message": "Cursor parameter is required",
#                         "data": [],
#                     }
#                 },
#             ),
#             500: openapi.Response(
#                 description="Server error",
#                 examples={
#                     "application/json": {
#                         "status": False,
#                         "message": "Error loading products: internal error",
#                         "data": [],
#                     }
#                 },
#             ),
#         },
#         tags=["Home Products"],
#     )
    
#     def get(self, request):
#         """
#         Fetch next batch of products using cursor for infinite scroll
#         """
#         cursor = request.GET.get('cursor')

#         if not cursor:
#             return Response({
#                 'status': False,
#                 'message': 'Cursor parameter is required',
#                 'data': []
#             }, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             cursor_id = int(cursor)
#             page_size = 12
#             all_products = []

#             tenants = DeliveryTenant.objects.filter(is_active=True)

#             # Fetch products for each tenant schema
#             for tenant in tenants:
#                 with schema_context(tenant.schema_name):
#                     products = Product.objects.filter(
#                         is_available=True,
#                         id__lt=cursor_id
#                     ).order_by('-created_date')[:page_size]
#                     serializer = ProductSerializer(products, many=True)

#                     for product_data in serializer.data:
#                         product_data['store_name'] = tenant.name
#                         product_data['store_domain'] = tenant.domains.first().domain if tenant.domains.exists() else None
#                         all_products.append(product_data)

#             next_cursor = all_products[-1]['id'] if all_products else None
#             has_next = len(all_products) == page_size

#             response_data = {
#                 'products': all_products,
#                 'has_next': has_next,
#                 'next_cursor': next_cursor,
#                 'count': len(all_products)
#             }

#             return Response({
#                 'status': True,
#                 'message': 'More products loaded successfully',
#                 'data': response_data
#             })

#         except ValueError:
#             return Response({
#                 'status': False,
#                 'message': 'Invalid cursor format',
#                 'data': []
#             }, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             return Response({
#                 'status': False,
#                 'message': f'Error loading products: {str(e)}',
#                 'data': []
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
