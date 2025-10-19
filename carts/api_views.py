# carts/api/views.py
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem
from store.models import Product, Variation
from .serializers import CartItemSerializer
from drf_yasg.utils import swagger_auto_schema


def _cart_id(request):
    """Generate or get session key for anonymous user"""
    cart_id = request.session.session_key
    if not cart_id:
        request.session.create()
        cart_id = request.session.session_key
    return cart_id


class CartItemListAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(operation_summary="List all cart items")
    def get(self, request):
        if request.user.is_authenticated:
            # Ensure user has a cart
            cart, _ = Cart.objects.get_or_create(user=request.user)
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        else:
            cart, _ = Cart.objects.get_or_create(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        serializer = CartItemSerializer(cart_items, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(operation_summary="Add product to cart")
    def post(self, request):
        product_id = request.data.get("product_id")
        quantity = int(request.data.get("quantity", 1))
        product = get_object_or_404(Product, id=product_id)

        if request.user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=request.user)
            cart_item, created = CartItem.objects.get_or_create(
                product=product,
                cart=cart,
                defaults={"user": request.user, "quantity": quantity}
            )
        else:
            cart, _ = Cart.objects.get_or_create(cart_id=_cart_id(request))
            cart_item, created = CartItem.objects.get_or_create(
                product=product,
                cart=cart,
                defaults={"quantity": quantity}
            )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CartItemDetailAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(operation_summary="Retrieve cart item details")
    def get(self, request, pk):
        cart_item = get_object_or_404(CartItem, id=pk)
        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data)

    @swagger_auto_schema(operation_summary="Update cart item quantity")
    def put(self, request, pk):
        cart_item = get_object_or_404(CartItem, id=pk)
        quantity = int(request.data.get("quantity", 1))
        if quantity <= 0:
            cart_item.delete()
            return Response({"detail": "Cart item deleted"}, status=status.HTTP_204_NO_CONTENT)
        cart_item.quantity = quantity
        cart_item.save()
        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data)

    @swagger_auto_schema(operation_summary="Delete cart item")
    def delete(self, request, pk):
        cart_item = get_object_or_404(CartItem, id=pk)
        cart_item.delete()
        return Response({"detail": "Cart item deleted"}, status=status.HTTP_204_NO_CONTENT)
