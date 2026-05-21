from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import ShippingAddress
from .serializers import ShippingAddressSerializer


class ShippingAddressAPIView(APIView):
    """
    GET:
        Retrieve authenticated user's shipping addresses.

    POST:
        Create a new shipping address
        for authenticated user.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):

        addresses = ShippingAddress.objects.filter(
            user=request.user
        )

        serializer = ShippingAddressSerializer(
            addresses,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def post(self, request):

        serializer = ShippingAddressSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save(
            user=request.user
        )

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )