from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from ..models import Product, Category, ReviewRating
from ..serializers import ProductSerializer, CategorySerializer, ReviewRatingSerializer

class TenantAwareViewSet(viewsets.ModelViewSet):
    """Base ViewSet that automatically filters by tenant"""
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # If user is merchant, filter by their tenant
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            if self.request.user.is_merchant_user and self.request.user.tenant:
                return queryset.filter(tenant=self.request.user.tenant)
        
        # If tenant is in request (from subdomain), filter by tenant
        if hasattr(self.request, 'tenant') and self.request.tenant:
            return queryset.filter(tenant=self.request.tenant)
        
        # Platform admin can see all (no filtering)
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            if self.request.user.is_platform_admin:
                return queryset
        
        # Default: return empty queryset for security
        return queryset.none()
    
    def perform_create(self, serializer):
        # Automatically set tenant for merchant users
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            if self.request.user.is_merchant_user and self.request.user.tenant:
                serializer.save(tenant=self.request.user.tenant)
            else:
                serializer.save()

class MerchantProductViewSet(TenantAwareViewSet):
    """Products API for merchants (with tenant filtering)"""
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_available']
    search_fields = ['product_name', 'description']
    ordering_fields = ['price', 'created_date', 'stock']
    
    def get_queryset(self):
        # Only merchant users can access
        if not self.request.user.is_merchant_user:
            return Product.objects.none()
        return Product.objects.filter(tenant=self.request.user.tenant)

class PublicProductViewSet(viewsets.ReadOnlyModelViewSet):
    """Public products API (read-only, tenant-aware)"""
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['product_name', 'description']
    ordering_fields = ['price', 'created_date']
    
    def get_queryset(self):
        # Filter by tenant from subdomain
        if hasattr(self.request, 'tenant') and self.request.tenant:
            return Product.objects.filter(
                tenant=self.request.tenant, 
                is_available=True
            )
        return Product.objects.none()  # No tenant = no products