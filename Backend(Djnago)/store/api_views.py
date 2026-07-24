
from django.db import transaction
from rest_framework.pagination import CursorPagination
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from django_tenants.utils import schema_context

from merchant_user.models import Organization
from store.models import Product
from store.serializers import (
    ProductCreateSerializer,
    ProductListSerializer,
)

class ProductCursorPagination(CursorPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
    
    # Stable ordering
    ordering = ("-created_date", "-id")



class ProductAPIView(APIView):
    
    def get(self, request):
        organization_id  = request.query_params.get("organization_id")

        if not organization_id:
            raise ValidationError("organization_id is required")

        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            raise ValidationError("Invalid organization_id")
        
        with schema_context(organization.schema_name):
            queryset = (
                Product.objects
                .filter(
                    organization=organization,
                    is_available=True,
                )
                .select_related("category")
                .only(
                    "id",
                    "product_name",
                    "slug",
                    "price",
                    "mrp",
                    "images",
                    "stock",
                    "is_available",
                    "category",
                    "created_date",
                )
                .order_by("-created_date")
            )

            # Category Filter
            category = request.query_params.get("category")
            if category:
                queryset = queryset.filter(category_id=category)

            # Search
            search = request.query_params.get("search")
            if search:
                queryset = queryset.filter(product_name__icontains=search)

            paginator =  ProductCursorPagination()
            page = paginator.paginate_queryset(queryset, request)

            serializer = ProductListSerializer(page, many=True)
            return_data = paginator.get_paginated_response(serializer.data)
            print("return_data", return_data.data)

            return return_data

    
    def post(self, request):
        organization = getattr(request, "organization", None)
        if not organization:
            raise ValidationError("organization_id is required")
        
        with transaction.atomic():
            serializer = ProductCreateSerializer(
                data=request.data,
                context={"organization": organization}
            )
            serializer.is_valid(raise_exception=True)
            product = serializer.save()

        return Response({
            "message": "Product added successfully",
            "data": serializer.data
        }, status=201)
    