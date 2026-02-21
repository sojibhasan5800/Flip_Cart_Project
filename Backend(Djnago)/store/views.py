from django.shortcuts import render, get_object_or_404, redirect
# from .models import Product,ReviewRating,ProductGallery
# from category.models import Category
# from carts.models import CartItem
# from django.db.models import Q
# from accounts.models import UserProfile
# import requests
# from django.utils.text import slugify
# from django.core.files.base import ContentFile
# from urllib.parse import urlparse
# import os
# from orders.utils import send_order_to_queue
# from rest_framework.response import Response


# from carts.views import _cart_id
# from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
# from django.http import HttpResponse
# from .forms import ReviewForm
# from django.contrib import messages
# from orders.models import OrderProduct
# from django.http import HttpResponse
# import cloudinary.uploader 
# from rest_framework.authtoken.models import Token
# from urllib.parse import urljoin
# from urllib.parse import urlparse
# from .recommendation_engine import get_similar_products
# from django_redis import get_redis_connection
# import json

# from django.db.models import F, Value, Func, CharField
# from django.db.models.functions import Concat
# from .documents import ProductDocument
# from rest_framework.views import APIView

def store(request, category_slug=None):
    return render(request, 'base.html')


# def product_detail(request, category_slug, product_slug):
#     try:
#         single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
#         in_cart = CartItem.objects.filter(cart__cart_id = _cart_id(request),product=single_product).exists()
        
#     except Exception as e:
#         raise e

#     if request.user.is_authenticated:
#         try:
#             orderproduct = OrderProduct.objects.filter(user=request.user, product_id=single_product.id).exists()
#         except OrderProduct.DoesNotExist:
#             orderproduct = None
#     else:
#         orderproduct = None

#     # Get the reviews
#     reviews = ReviewRating.objects.filter(product_id=single_product.id, status=True).order_by('-rating', '-created_at') 

#     # Get the product gallery
#     product_gallery = ProductGallery.objects.filter(product_id=single_product.id)
#     colors =None
#     sizes = None
#     try:
#         colors = single_product.variation_set.colors()
#     except Exception:
#         colors = None

#     try:
#         sizes = single_product.variation_set.sizes()
#     except Exception:
#         sizes = None

#     similar_product_id = single_product.id
#     similar_product = get_similar_products(similar_product_id)

#     # Fetch reviews from Redis
#     cache = get_redis_connection("default")
#     cached_reviews = cache.get(f'product_reviews:{single_product.id}')
#     if cached_reviews:
#         reviews = json.loads(cached_reviews)
#     else:
#         reviews_qs  = single_product.reviewrating_set.all().annotate(
#             full_name=Concat(F('user__first_name'), Value(' '), F('user__last_name'), output_field=CharField())
#         ).values('full_name', 'rating', 'subject', 'review', 'updated_at').order_by('-rating', '-updated_at')
#         reviews = []
#         for r in reviews_qs:
#             reviews.append({
#                 'full_name': r['full_name'],
#                 'rating': r['rating'],
#                 'subject': r['subject'],
#                 'review': r['review'],
#                 'updated_at': r['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
#             })
#         cache.set(f'product_reviews:{single_product.id}', json.dumps(reviews), ex=3600)
        
    
#     context = {
#         'single_product': single_product,
#         'in_cart'       : in_cart,
#         'orderproduct': orderproduct,
#         'reviews': reviews,
#         'product_gallery': product_gallery,
#         'colors':colors,
#         'sizes':sizes,
#         'similar_product': similar_product
#     }
#     return render(request, 'store/product_detail.html', context)




# class ProductSearchView(APIView):
#     def get(self, request):
#         search = request.GET.get('search')
#         if not search:
#             return Response({
#                 'status': False,
#                 'message': 'Search query is required',
#                 'data': []
#             })

#         products = []

#         # price remove from multi_match fields
#         results = ProductDocument.search().query(
#             'multi_match',
#             query=search,
#             fields=['product_name', 'description'],  # <-- price removed
#             fuzziness="AUTO",
#             operator="OR",
#             type='best_fields'
#         ).extra(size=8)

#         results = results.execute()

#         for result in results:
#             products.append({
#                 'id': result.id,
#                 'product_name': result.product_name,
#                 'description': getattr(result, 'description', ''),
#                 'price': getattr(result, 'price', 0)
#             })
#         return Response({
#             'status': True,
#             'message': 'Products fetched',
#             'data': products
#         })


# def search(request):
#     if 'keyword' in request.GET:
#         keyword = request.GET['keyword']        

#         # for result in results
        
#         if keyword:
#             products = Product.objects.order_by('-created_date').filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword))
#             product_count = products.count()
#     context = {
#         'products': products,
#         'product_count': product_count,
#     }
#     return render(request, 'store/store.html', context)

# from django.contrib import messages
# from django.shortcuts import redirect, get_object_or_404
# from .forms import ReviewForm
# from .models import ReviewRating, Product

# def submit_review(request, product_id):
#     # Get the referring URL to redirect back after submitting
#     url = request.META.get('HTTP_REFERER')  
#     product = get_object_or_404(Product, id=product_id)

#     if request.method == 'POST':
#         try:
#             # Check if the user has already submitted a review for this product
#             review = ReviewRating.objects.get(user=request.user, product=product)
#             form = ReviewForm(request.POST, instance=review)
#             if form.is_valid():
#                 # Update existing review
#                 form.save()
#                 payload = {
#                 "event_type": "product.review",
#                 "product_id": product.id,
#                 "product_name": product.product_name,
#                 "user_id": request.user.id,
#                 "rating": review.rating, 
#                 "created_at": review.created_at.isoformat() if hasattr(review,'created_at') else None
#                 }
#                 send_order_to_queue(payload)
#                 messages.success(request, 'Thank you! Your review has been updated.')
#             else:
#                 messages.error(request, 'There was an error updating your review.')
#         except ReviewRating.DoesNotExist:
#             # Create a new review if one does not exist
#             form = ReviewForm(request.POST)
#             if form.is_valid():
#                 new_review = ReviewRating()
#                 new_review.subject = form.cleaned_data['subject']
#                 new_review.rating = form.cleaned_data['rating']
#                 new_review.review = form.cleaned_data['review']
#                 new_review.ip = request.META.get('REMOTE_ADDR')
#                 new_review.product = product
#                 new_review.user = request.user
#                 new_review.status = True  # Make the review active
#                 new_review.save()
#                 messages.success(request, 'Thank you! Your review has been submitted.')
#             else:
#                 messages.error(request, 'There was an error submitting your review.')

#     # Redirect back to the same page
#     return redirect(url)

            
# def load_product_object(request):

#     product_url = 'https://dummyjson.com/products'
#     response = requests.get(url=product_url, timeout=15)
#     api_data = response.json()
#     product_data = api_data.get('products', [])
#     print("Loaded product data from API ")

#     for item in product_data:
#         title = item.get('title', '')
#         slug = slugify(title)
#         description = item.get('description', '')
#         price = int(float(item.get('price', 0)))
#         stock = item.get('stock', 0)
#         thumbnail_url = item.get('thumbnail', None)
#         image_urls = item.get('images', [])
#         category_name = item.get('category', 'Uncategorized')

#         # Ensure category is created or fetched
#         category_obj, _ = Category.objects.get_or_create(
#             slug=slugify(category_name),
#             defaults={'category_name': category_name}
#         )

#         # Check existing product
#         if Product.objects.filter(slug=slug).exists() or Product.objects.filter(product_name=title).exists():
#             continue

#         # Thumbnail upload (optional)
#         image_url = None
#         if thumbnail_url:
#             try:
#                 uploaded_thumb = cloudinary.uploader.upload(thumbnail_url)
#                 image_url = uploaded_thumb.get('secure_url')
#             except Exception as e:
#                 print("Thumbnail upload failed:", e)

#         # ✅ Product create
#         product = Product.objects.create(
#             product_name=title,
#             slug=slug,
#             description=description,
#             price=price,
#             stock=stock,
#             is_available=(stock > 0),
#             category=category_obj,
#         )

#         # Save product main image
#         if image_url:
#             product.images = image_url
#             product.save()

#         # Gallery images upload
#         for img_url in image_urls:
#             try:
#                 uploaded_img = cloudinary.uploader.upload(img_url)
#                 gallery_img_url = uploaded_img.get('secure_url')
#                 ProductGallery.objects.create(product=product, image=gallery_img_url)
#             except Exception as e:
#                 print("Gallery upload failed:", e)
#                 continue

#     print(" All products successfully loaded from API!")
#     return redirect('home')  # only runs once
