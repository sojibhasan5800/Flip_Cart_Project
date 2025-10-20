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


def _user_cart_id(user):
    """Generate unique cart_id for logged-in user"""
    return f"user_{user.id}"

class CartItemListAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    
    @swagger_auto_schema(operation_summary="Retrieve cart items by cart PK (handles both guest and authenticated users safely)")
    
    def get(self, request):
        try:
            #  Step 1: Get cart id from query param
            pk = request.query_params.get('id', None)

            if not pk:
                return Response(
                    {"detail": "Please provide ?id=<cart_id> in query params."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Case 1: Authenticated user – use user's cart directly
            if request.user.is_authenticated:
                cart = Cart.objects.filter(pk=pk).first()
            else:
                # Case 2: Guest user – verify session cart_id
                session_cart_id = _cart_id(request)
                cart = Cart.objects.filter(cart_id=session_cart_id, pk=pk).first()

            # No cart found
            if not cart:
                return Response(
                    {"detail": "Cart not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Fetch active cart items
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)

            if not cart_items.exists():
                return Response(
                    {"detail": "Cart is empty."},
                    status=status.HTTP_204_NO_CONTENT
                )

            serializer = CartItemSerializer(cart_items, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        


    @swagger_auto_schema(operation_summary="Add product to cart")
    def post(self, request):
        product_id = request.data.get("product_id")
        quantity = int(request.data.get("quantity", 1))
        product = get_object_or_404(Product, id=product_id)

        if request.user.is_authenticated:
            # Logged-in user
            cart_id = _user_cart_id(request.user)
            cart, _ = Cart.objects.get_or_create(cart_id=cart_id)

            # Merge guest cart if exists
            session_cart_id = _cart_id(request)
            try:
                session_cart = Cart.objects.get(cart_id=session_cart_id)
                guest_items = CartItem.objects.filter(cart=session_cart, is_active=True)
                for item in guest_items:
                    user_item, created = CartItem.objects.get_or_create(
                        product=item.product,
                        cart=cart,
                        defaults={"user": request.user, "quantity": item.quantity}
                    )
                    if not created:
                        user_item.quantity += item.quantity
                        user_item.save()
                    item.delete()
                session_cart.delete()
            except Cart.DoesNotExist:
                pass

            # Add product to user cart
            cart_item, created = CartItem.objects.get_or_create(
                product=product,
                cart=cart,
                defaults={"user": request.user, "quantity": quantity}
            )
        else:
            # Guest user
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
