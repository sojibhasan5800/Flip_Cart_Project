# # carts/api/views.py
# from rest_framework import permissions, status
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from django.shortcuts import get_object_or_404
# from .models import Cart, CartItem
# from store.models import Product, Variation
# from .serializers import CartItemSerializer
# from drf_yasg.utils import swagger_auto_schema
# import uuid


# def _cart_id(request):
#     """Generate or get session key for anonymous user"""
#     cart_id = request.session.session_key
#     if not cart_id:
#         request.session.create()
#         cart_id = request.session.session_key
#     return cart_id


# def _user_cart_id(user):
#     """Generate unique cart_id for logged-in user"""
#     return f"{user.id}_{uuid.uuid4().hex[:8]}" 

# class CartItemListAPIView(APIView):
#     permission_classes = [permissions.AllowAny]

#     @swagger_auto_schema(operation_summary="Retrieve cart items by cart PK (optimized response)")
#     def get(self, request):
#         try:
#             pk = request.query_params.get('id', None)
#             if not pk:
#                 return Response(
#                     {"detail": "Please provide ?id=<cart_id> in query params."},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#             if request.user.is_authenticated:
#                 cart = Cart.objects.filter(cart_id=pk).first()
#             else:
#                 session_cart_id = _cart_id(request)
#                 cart = Cart.objects.filter(cart_id=session_cart_id, pk=pk).first()

#             if not cart:
#                 return Response({"detail": "Cart not found."}, status=status.HTTP_404_NOT_FOUND)

#             cart_items = CartItem.objects.filter(cart=cart, is_active=True)
#             if not cart_items.exists():
#                 return Response({"detail": "Cart is empty."}, status=status.HTTP_204_NO_CONTENT)

#             # Calculate totals
#             total = sum(item.product.price * item.quantity for item in cart_items)
#             quantity = sum(item.quantity for item in cart_items)
#             discount = total * 0.05
#             grand_total = total - discount

#             # Prepare optimized cart_items response
#             cart_items_data = []
#             for item in cart_items:
#                 cart_items_data.append({
#                     "id": item.id,
#                     "product": {
#                         "id": item.product.id,
#                         "name": item.product.product_name,
#                         "slug": item.product.slug,
#                         "price": item.product.price,
#                         "images": item.product.images.url if item.product.images else None,
#                         "stock": item.product.stock,
#                         "is_available": item.product.is_available,
#                     },
#                     "variations": [{"id": v.id, "name": v.variation_value} for v in item.variations.all()],
#                     "quantity": item.quantity,
#                     "sub_total": item.sub_total()
#                 })
#             # Include user info once at top-level
#             user_data = None
#             if request.user.is_authenticated:
#                 user_data = {
#                     "id": request.user.id,
#                     "first_name": request.user.first_name,
#                     "last_name": request.user.last_name,
#                     "email": request.user.email,
#                     "phone_number": request.user.phone_number,
#                 }

#             response_data = {
#                 "user": user_data,
#                 "cart_id": cart.cart_id,
#                 "cart_items": cart_items_data,
#                 "total": total,
#                 "quantity": quantity,
#                 "discount": discount,
#                 "grand_total": grand_total,
#             }

#             return Response(response_data, status=status.HTTP_200_OK)

#         except Exception as e:
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


#     @swagger_auto_schema(operation_summary="Add product to cart (minimal response)")
#     def post(self, request):
#         product_id = request.data.get("product_id")
#         quantity = int(request.data.get("quantity", 1))
#         product = get_object_or_404(Product, id=product_id)

#         if request.user.is_authenticated:
#             cart = Cart.objects.filter(cart_id__startswith=f"{request.user.id}_").first()

#             if not cart:
#                 cart_id = _user_cart_id(request.user)
#                 cart = Cart.objects.create(cart_id=cart_id)

#             # Merge guest cart if exists
#             session_cart_id = _cart_id(request)
#             try:
#                 session_cart = Cart.objects.get(cart_id=session_cart_id)
#                 guest_items = CartItem.objects.filter(cart=session_cart, is_active=True)
#                 for item in guest_items:
#                     user_item, created = CartItem.objects.get_or_create(
#                         product=item.product,
#                         cart=cart,
#                         defaults={"user": request.user, "quantity": item.quantity}
#                     )
#                     if not created:
#                         user_item.quantity += item.quantity
#                         user_item.save()
#                     item.delete()
#                 session_cart.delete()
#             except Cart.DoesNotExist:
#                 pass

#             # Add product to user cart
#             cart_item, created = CartItem.objects.get_or_create(
#                 product=product,
#                 cart=cart,
#                 defaults={"user": request.user, "quantity": quantity}
#             )
#         else:
#             # Guest user
#             cart, _ = Cart.objects.get_or_create(cart_id=_cart_id(request))
#             cart_item, created = CartItem.objects.get_or_create(
#                 product=product,
#                 cart=cart,
#                 defaults={"quantity": quantity}
#             )

#         if not created:
#             cart_item.quantity += quantity
#             cart_item.save()

#         # Prepare minimal response for the newly added cart item
#         response_data = {
#             "cart_item": {
#                 "id": cart_item.id,
#                 "product": {
#                     "id": cart_item.product.id,
#                     "name": cart_item.product.product_name,
#                     "slug": cart_item.product.slug,
#                     "price": cart_item.product.price,
#                     "images": cart_item.product.images.url if cart_item.product.images else None,
#                     "stock": cart_item.product.stock,
#                     "is_available": cart_item.product.is_available,
#                 },
#                 "variations": [{"id": v.id, "name": v.variation_value} for v in cart_item.variations.all()],
#                 "quantity": cart_item.quantity,
#                 "cart_id": cart.cart_id,
#                 # "sub_total": cart_item.sub_total(),
#             }
#         }

#         return Response(response_data, status=status.HTTP_201_CREATED)



# class CartItemDetailAPIView(APIView):
#     permission_classes = [permissions.AllowAny]

#     @swagger_auto_schema(operation_summary="Update cart item quantity")
#     def put(self, request, pk):
#         cart_item = get_object_or_404(CartItem, id=pk)
#         quantity = int(request.data.get("quantity", 1))
#         if quantity <= 0:
#             cart_item.delete()
#             return Response({"detail": "Cart item deleted"}, status=status.HTTP_204_NO_CONTENT)
#         cart_item.quantity = quantity
#         cart_item.save()
#         serializer = CartItemSerializer(cart_item)
#         return Response(serializer.data)

#     @swagger_auto_schema(operation_summary="Delete cart item")
#     def delete(self, request, pk):
#         cart_item = get_object_or_404(CartItem, id=pk)
#         cart_item.delete()
#         return Response({"detail": "Cart item deleted"}, status=status.HTTP_204_NO_CONTENT)


# class CheckoutAPIView(APIView):
#     # Allow both authenticated and guest users to access checkout
#     permission_classes = [permissions.IsAuthenticatedOrReadOnly]

#     @swagger_auto_schema(operation_summary="Retrieve checkout summary (calculate total, discount, grand total using cart ID)")
#     def get(self, request):
#         try:
#             total = 0
#             quantity = 0
#             discount = 0
#             grand_total = 0
#             cart_items = None

#             # Step 1: Get cart_id from query parameters
#             cart_id = request.query_params.get('cart_id', None)

#             if request.user.is_authenticated:
#                 # Case 1: Logged-in user – get items linked to the authenticated user
#                 cart_items = CartItem.objects.filter(user=request.user, is_active=True)
#             else:
#                 # Case 2: Guest user – use cart_id from session or query param
#                 if not cart_id:
#                     return Response(
#                         {"detail": "Please provide ?cart_id=<id> in query params."},
#                         status=status.HTTP_400_BAD_REQUEST
#                     )
#                 cart = Cart.objects.filter(cart_id=cart_id).first()
#                 if not cart:
#                     return Response({"detail": "Cart not found."}, status=status.HTTP_404_NOT_FOUND)
#                 cart_items = CartItem.objects.filter(cart=cart, is_active=True)

#             # Step 2: Handle empty cart
#             if not cart_items.exists():
#                 return Response({"detail": "Cart is empty."}, status=status.HTTP_204_NO_CONTENT)

#             # Step 3: Calculate totals
#             for item in cart_items:
#                 total += item.product.price * item.quantity
#                 quantity += item.quantity

#             # 5% discount example
#             discount = (5 * total) / 100
#             grand_total = total - discount

#             # Step 4: Serialize and return checkout data
#             serializer = CartItemSerializer(cart_items, many=True)
#             response_data = {
#                 "cart_items": serializer.data,
#                 "total": total,
#                 "quantity": quantity,
#                 "discount": discount,
#                 "grand_total": grand_total,
#             }

#             return Response(response_data, status=status.HTTP_200_OK)

#         except Exception as e:
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
