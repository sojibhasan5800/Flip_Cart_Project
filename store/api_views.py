# store/api/views.py
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Product, ReviewRating, ProductGallery, Variation
from .serializers import ProductSerializer, ReviewRatingSerializer, ProductGallerySerializer, VariationSerializer
from django_redis import get_redis_connection
from django.db.models import F, Value, CharField
from django.db.models.functions import Concat
import json

# ------------------ Product APIs ------------------
class ProductListCreateAPIView(generics.ListCreateAPIView):
    queryset = Product.objects.all().order_by('-created_date')
    serializer_class = ProductSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            # Only admin can create
            return [permissions.IsAdminUser()]
        # Any authenticated user can list
        return [permissions.IsAuthenticated()]

class ProductDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            # Only admin can update/delete
            return [permissions.IsAdminUser()]
        # Any authenticated user can view
        return [permissions.IsAuthenticated()]

# ------------------ Review APIs ------------------
class ReviewRatingListAPIView(generics.ListAPIView):
    serializer_class = ReviewRatingSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = ReviewRating.objects.filter(status=True).order_by('-created_at')
        product_id = self.request.query_params.get('product')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        return queryset

class ReviewRatingCreateAPIView(generics.CreateAPIView):
    serializer_class = ReviewRatingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        product_id = self.request.data.get('product')
        product = get_object_or_404(Product, id=product_id)
        review = serializer.save(user=self.request.user, product=product, status=True)
        
        # Update Redis cache
        cache = get_redis_connection("default")
        reviews_qs = list(product.reviewrating_set.annotate(
            full_name=Concat(F('user__first_name'), Value(' '), F('user__last_name'), output_field=CharField())
        ).values('full_name', 'rating', 'subject', 'review', 'updated_at').order_by('-rating', '-updated_at'))
        reviews = [{'full_name': r['full_name'], 'rating': r['rating'], 'subject': r['subject'], 'review': r['review'], 'updated_at': r['updated_at'].strftime('%Y-%m-%d %H:%M:%S')} for r in reviews_qs]
        cache.set(f'product_reviews:{product.id}', json.dumps(reviews), ex=3600)

# ------------------ Product Gallery APIs ------------------
class ProductGalleryListCreateAPIView(generics.ListCreateAPIView):
    queryset = ProductGallery.objects.all()
    serializer_class = ProductGallerySerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            # Only admin can create
            return [permissions.IsAdminUser()]
        # Any authenticated user can list
        return [permissions.IsAuthenticated()]

class ProductGalleryDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProductGallery.objects.all()
    serializer_class = ProductGallerySerializer

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            # Only admin can update or delete
            return [permissions.IsAdminUser()]
        # Any authenticated user can retrieve
        return [permissions.IsAuthenticated()]

# ------------------ Variation APIs ------------------
class VariationListCreateAPIView(generics.ListCreateAPIView):
    queryset = Variation.objects.all()
    serializer_class = VariationSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]
    

class VariationDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Variation.objects.all()
    serializer_class = VariationSerializer

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]
    
# ------------------ Product Search API ------------------
from .documents import ProductDocument
from rest_framework import filters

class ProductSearchAPIView(APIView):
    def get(self, request):
        query = request.GET.get('search')
        if not query:
            return Response({'status': False, 'message': 'Search query is required', 'data': []})
        
        results = ProductDocument.search().query(
            'multi_match',
            query=query,
            fields=['product_name', 'description'],
            fuzziness="AUTO",
            operator="OR",
            type='best_fields'
        ).extra(size=10).execute()

        products = [{'id': r.id, 'product_name': r.product_name, 'description': getattr(r, 'description',''), 'price': getattr(r,'price',0)} for r in results]
        return Response({'status': True, 'message': 'Products fetched', 'data': products})
