from rest_framework import generics, permissions

from orders_management.models.address import ShippingAddress
from .serializers import  ShippingAddressSerializer


class ShippingAddressCreateAPIView(generics.ListCreateAPIView):

    serializer_class = ShippingAddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ShippingAddress.objects.filter(
            user=self.request.user
        )

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user
        )