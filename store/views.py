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

#--------------------- Api Import -------------------------------------
# from rest_framework import viewsets, permissions, filters,mixins,pagination
# from rest_framework.generics import ListAPIView,CreateAPIView
# from .serializers import ProductSerializer,ReviewRatingSerializer
# from rest_framework.permissions import IsAuthenticatedOrReadOnly,IsAuthenticated
# from django_filters.rest_framework import DjangoFilterBackend
# from rest_framework.authtoken.models import Token
# from urllib.parse import urljoin
# from urllib.parse import urlparse
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

    
    context = {
        'single_product': single_product,
        'in_cart'       : in_cart,
        'orderproduct': orderproduct,
        'reviews': reviews,
        'product_gallery': product_gallery,
        'colors':colors,
        'sizes':sizes
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


def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER')
    if request.method == 'POST':
        try:
            reviews = ReviewRating.objects.get(user__id=request.user.id, product__id=product_id)
            form = ReviewForm(request.POST, instance=reviews)
            form.save()
            messages.success(request, 'Thank you! Your review has been updated.')
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                # data = ReviewRating()
                # data.subject = form.cleaned_data['subject']
                # data.rating = form.cleaned_data['rating']
                # data.review = form.cleaned_data['review']
                # data.ip = request.META.get('REMOTE_ADDR')
                # data.product_id = product_id
                # data.user_id = request.user.id
                # data.save()
            # APi Throug Saving Data :
                
                subject = form.cleaned_data['subject']
                rating = form.cleaned_data['rating']
                review = form.cleaned_data['review']
                ip = request.META.get('REMOTE_ADDR')
                user_id = request.user.id
                token = Token.objects.get(user=request.user)
                #----------------------------
                parsed_url = urlparse(url)
                base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"  # http://127.0.0.1:8000
                full_url = urljoin(base_url, "/store/review_list_api/create/")  # full API URL
                review_url = full_url           
                headers = {
                    "Authorization": f"Token {token.key}",
                    "Content-Type": "application/json"
                }
                data = {
                    "product": product_id,
                    "subject": subject,
                    "review": review,
                    "rating": rating,
                }
                response = requests.post(review_url, json=data, headers=headers)

                if response.status_code == 201:
                    messages.success(request, 'Thank you! Your review has been submitted.')
                else:
                    print("API Error Response:", response.status_code, response.text)
                    messages.error(request, 'Failed to submit review. Please try again.')
                
                return redirect(url)
            
def load_product_object(request):
    product_url = 'https://dummyjson.com/products'
    response = requests.get(url=product_url)
    api_data = response.json()
    product_data = api_data.get('products',[])
    print("loaded producted !!!!!!!!!")

    for item in product_data:
        title = item.get('title')
        slug = slugify(title)
        description = item.get('description')
        price = int(float(item.get('price', 0)))
        stock = item.get('stock', 0)
        thumbnail_url = item.get('thumbnail',None)
        image_urls = item.get('images', [])
        category_name = item.get('category')

        # check category: 

        try:
            category_obj = Category.objects.get(slug=slugify(category_name))
        except Category.DoesNotExist:
            continue

        # skip same product:

        if Product.objects.filter(product_name=title).exists():
            continue

      
        # Thumbail Download
        image_file = None
        image_name = None
        image_url = None
        if thumbnail_url:
            try:
                uploaded_thumb = cloudinary.uploader.upload(thumbnail_url)
                image_url = uploaded_thumb.get('secure_url')  # Cloud URL
            except:
                continue

        product = Product.objects.create(
            product_name=title,
            slug=slug,
            description=description,
            price=price,
            stock=stock,
            is_available=(stock > 0),
            category=category_obj,
        )

        #  Save Image URL in CloudinaryField
        if image_url:
            product.images = image_url
            product.save()

        #   ProductGallery image uploads
        for img_url in image_urls:
            try:
                uploaded_img = cloudinary.uploader.upload(img_url)
                gallery_img_url = uploaded_img.get('secure_url')
                ProductGallery.objects.create(product=product, image=gallery_img_url)
            except:
                continue            

    print("All Api Product is Loaded!!!!!")
    return redirect('home')
