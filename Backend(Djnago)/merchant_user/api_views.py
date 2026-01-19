
from httpcore import request
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone

from merchant_user.models import Organization, MerchantUser
from .serializers import OrganizationCreateSerializer
from rest_framework.permissions import IsAuthenticated
from django_tenants.utils import schema_context
from django.db import transaction


class MerchantStoreCreateAPIView(APIView):
    """
    Merchant Store Create & Status API

    GET:
    - Check if merchant already submitted a store
    - Returns status: pending / approved / rejected

    POST:
    - Submit new store application
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        merchant_profile = MerchantUser.objects.filter(user=user).first()
        if not merchant_profile or not merchant_profile.organization:
            return Response(
                {"status": None},
                status=status.HTTP_200_OK
            )

        organization = merchant_profile.organization

        if organization.is_verified:
            store_status = "approved"
        elif organization.is_active:
            store_status = "pending"
        else:
            store_status = "rejected"

        return Response(
            {
                "status": store_status,
                "store_name": organization.business_name,
            },
            status=status.HTTP_200_OK
        )

    def post(self, request):
        user = request.user

        # Prevent duplicate store creation
        if MerchantUser.objects.filter(user=user).exists():
            return Response(
                {"error": "Store already submitted."},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = OrganizationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Create merchant profile (Owner)
        with schema_context('public'), transaction.atomic():
                # এখানে serializer.save() করলে public schema-তে create হবে
                organization = serializer.save()

                MerchantUser.objects.create(
                    user=user,
                    organization=organization,
                    role="owner",
                    is_active=True,
                    is_verified=False,
                )

        return Response(
            {
                "message": "Store application submitted successfully.",
                "status": "pending"
            },
            status=status.HTTP_201_CREATED
        )
    
