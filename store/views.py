from django.shortcuts import render, get_object_or_404, redirect
from .models import Product,ReviewRating,ProductGallery
from category.models import Category
from carts.models import CartItem
from django.db.models import Q
from accounts.models import UserProfile
import requests
from django.utils.text import slugify
from django.core.files.base import ContentFile
from urllib.parse import urlparse
import os


from carts.views import _cart_id
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import HttpResponse
from .forms import ReviewForm
from django.contrib import messages
from orders.models import OrderProduct
from django.http import HttpResponse
import cloudinary.uploader 
from rest_framework.authtoken.models import Token
from urllib.parse import urljoin
from urllib.parse import urlparse
from .recommendation_engine import get_similar_products

#--------------------- Api Import -------------------------------------
# from rest_framework import viewsets, permissions, filters,mixins,pagination
# from rest_framework.generics import ListAPIView,CreateAPIView
# from .serializers import ProductSerializer,ReviewRatingSerializer
# from rest_framework.permissions import IsAuthenticatedOrReadOnly,IsAuthenticated
# from django_filters.rest_framework import DjangoFilterBackend
# from rest_framework.authentication import TokenAuthentication



#--------------------- Api Create -------------------------------------
# ================= Pagination =================
# class StandardResultsSetPagination(pagination.PageNumberPagination):
#     page_size = 5
#     page_size_query_param = 'page_size'
#     max_page_size = 1000

# # ================= Product API =================
# class ProductViewSet(viewsets.ModelViewSet):
#     queryset = Product.objects.all().order_by('-created_date')
#     serializer_class = ProductSerializer
#     permission_classes = [IsAuthenticatedOrReadOnly]
#     filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
#     filterset_fields = ['category', 'price', 'stock', 'is_available']
#     search_fields = ['product_name', 'description']
#     ordering_fields = ['price', 'stock', 'created_date']
#     pagination_class = StandardResultsSetPagination

#     def list(self, request, *args, **kwargs):
#         queryset = self.filter_queryset(self.get_queryset())
#         page = self.paginate_queryset(queryset)
#         if page is not None:
#             serializer = self.get_serializer(page, many=True)
#             return self.get_paginated_response(serializer.data)
#         serializer = self.get_serializer(queryset, many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)

#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     def retrieve(self, request, *args, **kwargs):
#         instance = self.get_object()
#         serializer = self.get_serializer(instance)
#         return Response(serializer.data, status=status.HTTP_200_OK)

#     def update(self, request, *args, **kwargs):
#         partial = kwargs.pop('partial', False)
#         instance = self.get_object()
#         serializer = self.get_serializer(instance, data=request.data, partial=partial)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     def destroy(self, request, *args, **kwargs):
#         instance = self.get_object()
#         instance.delete()
#         return Response({"message": "Product deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


# # ================= Review List API =================
# class ReviewRatingListAPIView(ListAPIView):
#     queryset = ReviewRating.objects.filter(status=True).order_by('-created_at')
#     serializer_class = ReviewRatingSerializer
#     pagination_class = StandardResultsSetPagination

#     def get_queryset(self):
#         queryset = super().get_queryset()
#         product_id = self.request.query_params.get('product')
#         if product_id:
#             queryset = queryset.filter(product_id=product_id)
#         return queryset

#     def list(self, request, *args, **kwargs):
#         queryset = self.get_queryset()
#         page = self.paginate_queryset(queryset)
#         if page is not None:
#             serializer = self.get_serializer(page, many=True)
#             return self.get_paginated_response(serializer.data)
#         serializer = self.get_serializer(queryset, many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)


# # ================= Review Create API =================
# class ReviewRatingCreateAPIView(CreateAPIView):
#     queryset = ReviewRating.objects.all()
#     serializer_class = ReviewRatingSerializer
#     permission_classes = [IsAuthenticated]
#     authentication_classes = [TokenAuthentication]   

#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         if serializer.is_valid():
#             product_id = request.data.get("product")
#             product = get_object_or_404(Product, id=product_id)
#             serializer.save(
#                 user=request.user,
#                 ip=request.META.get('REMOTE_ADDR'),
#                 status=True,
#                 product=product
#             )
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# ------------------------------------------------------------------------


def store(request, category_slug=None):
    categories = None
    products = None

    if category_slug != None:
        categories = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(category=categories, is_available=True)
        paginator = Paginator(products, 2)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        product_count = products.count()
    else:
        products = Product.objects.all().filter(is_available=True).order_by('id')
        paginator = Paginator(products, 3)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        product_count = products.count()

    context = {
        'products': paged_products,
        'product_count': product_count,
    }
    return render(request, 'store/store.html', context)


def product_detail(request, category_slug, product_slug):
    try:
        single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
        in_cart = CartItem.objects.filter(cart__cart_id = _cart_id(request),product=single_product).exists()
        
    except Exception as e:
        raise e

    if request.user.is_authenticated:
        try:
            orderproduct = OrderProduct.objects.filter(user=request.user, product_id=single_product.id).exists()
        except OrderProduct.DoesNotExist:
            orderproduct = None
    else:
        orderproduct = None

    # Get the reviews
    reviews = ReviewRating.objects.filter(product_id=single_product.id, status=True)

    # Get the product gallery
    product_gallery = ProductGallery.objects.filter(product_id=single_product.id)
    colors =None
    sizes = None
    try:
        colors = single_product.variation_set.colors()
    except Exception:
        colors = None

    try:
        sizes = single_product.variation_set.sizes()
    except Exception:
        sizes = None

    similar_product_id = single_product.id
    similar_product = get_similar_products(similar_product_id)
    
    context = {
        'single_product': single_product,
        'in_cart'       : in_cart,
        'orderproduct': orderproduct,
        'reviews': reviews,
        'product_gallery': product_gallery,
        'colors':colors,
        'sizes':sizes,
        'similar_product': similar_product
    }
    return render(request, 'store/product_detail.html', context)


def search(request):
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            products = Product.objects.order_by('-created_date').filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword))
            product_count = products.count()
    context = {
        'products': products,
        'product_count': product_count,
    }
    return render(request, 'store/store.html', context)

from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from .forms import ReviewForm
from .models import ReviewRating, Product

def submit_review(request, product_id):
    # Get the referring URL to redirect back after submitting
    url = request.META.get('HTTP_REFERER')  
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        try:
            # Check if the user has already submitted a review for this product
            review = ReviewRating.objects.get(user=request.user, product=product)
            form = ReviewForm(request.POST, instance=review)
            if form.is_valid():
                # Update existing review
                form.save()
                messages.success(request, 'Thank you! Your review has been updated.')
            else:
                messages.error(request, 'There was an error updating your review.')
        except ReviewRating.DoesNotExist:
            # Create a new review if one does not exist
            form = ReviewForm(request.POST)
            if form.is_valid():
                new_review = ReviewRating()
                new_review.subject = form.cleaned_data['subject']
                new_review.rating = form.cleaned_data['rating']
                new_review.review = form.cleaned_data['review']
                new_review.ip = request.META.get('REMOTE_ADDR')
                new_review.product = product
                new_review.user = request.user
                new_review.status = True  # Make the review active
                new_review.save()
                messages.success(request, 'Thank you! Your review has been submitted.')
            else:
                messages.error(request, 'There was an error submitting your review.')

    # Redirect back to the same page
    return redirect(url)

            
def load_product_object(request):

    product_url = 'https://dummyjson.com/products'
    response = requests.get(url=product_url, timeout=15)
    api_data = response.json()
    product_data = api_data.get('products', [])
    print("Loaded product data from API ")

    for item in product_data:
        title = item.get('title', '')
        slug = slugify(title)
        description = item.get('description', '')
        price = int(float(item.get('price', 0)))
        stock = item.get('stock', 0)
        thumbnail_url = item.get('thumbnail', None)
        image_urls = item.get('images', [])
        category_name = item.get('category', 'Uncategorized')

        # Ensure category is created or fetched
        category_obj, _ = Category.objects.get_or_create(
            slug=slugify(category_name),
            defaults={'category_name': category_name}
        )

        # Check existing product
        if Product.objects.filter(slug=slug).exists() or Product.objects.filter(product_name=title).exists():
            continue

        # Thumbnail upload (optional)
        image_url = None
        if thumbnail_url:
            try:
                uploaded_thumb = cloudinary.uploader.upload(thumbnail_url)
                image_url = uploaded_thumb.get('secure_url')
            except Exception as e:
                print("Thumbnail upload failed:", e)

        # ✅ Product create
        product = Product.objects.create(
            product_name=title,
            slug=slug,
            description=description,
            price=price,
            stock=stock,
            is_available=(stock > 0),
            category=category_obj,
        )

        # Save product main image
        if image_url:
            product.images = image_url
            product.save()

        # Gallery images upload
        for img_url in image_urls:
            try:
                uploaded_img = cloudinary.uploader.upload(img_url)
                gallery_img_url = uploaded_img.get('secure_url')
                ProductGallery.objects.create(product=product, image=gallery_img_url)
            except Exception as e:
                print("Gallery upload failed:", e)
                continue

    print(" All products successfully loaded from API!")
    return redirect('home')  # only runs once
