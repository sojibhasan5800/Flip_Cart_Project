# carts/api/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem
from store.models import Product, Variation
from .serializers import CartSerializer, CartItemSerializer
from drf_yasg.utils import swagger_auto_schema

def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

# ---------------------------
# CartItem CRUD API
# ---------------------------
class CartItemListAPIView(APIView):
    """
    GET: List all cart items for user/session
    POST: Add product to cart
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(operation_summary="List all cart items")
    def get(self, request):
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart, _ = Cart.objects.get_or_create(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        serializer = CartItemSerializer(cart_items, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(operation_summary="Add product to cart")
    def post(self, request):
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)
        product = get_object_or_404(Product, id=product_id)

        # handle authenticated user
        if request.user.is_authenticated:
            cart_item, created = CartItem.objects.get_or_create(product=product, user=request.user)
        else:
            cart, _ = Cart.objects.get_or_create(cart_id=_cart_id(request))
            cart_item, created = CartItem.objects.get_or_create(product=product, cart=cart)

        if not created:
            cart_item.quantity += int(quantity)
            cart_item.save()

        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CartItemDetailAPIView(APIView):
    """
    PUT: Update cart item quantity
    DELETE: Remove cart item
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(operation_summary="Update cart item quantity")
    def put(self, request, pk):
        cart_item = get_object_or_404(CartItem, id=pk)
        quantity = int(request.data.get('quantity', 1))
        if quantity <= 0:
            cart_item.delete()
            return Response({"detail": "Cart item deleted"}, status=204)
        cart_item.quantity = quantity
        cart_item.save()
        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data)

    @swagger_auto_schema(operation_summary="Delete cart item")
    def delete(self, request, pk):
        cart_item = get_object_or_404(CartItem, id=pk)
        cart_item.delete()
        return Response({"detail": "Cart item deleted"}, status=204)
