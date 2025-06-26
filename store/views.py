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

    context = {
        'single_product': single_product,
        'in_cart'       : in_cart,
        'orderproduct': orderproduct,
        'reviews': reviews,
        'product_gallery': product_gallery,
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
                data = ReviewRating()
                data.subject = form.cleaned_data['subject']
                data.rating = form.cleaned_data['rating']
                data.review = form.cleaned_data['review']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request, 'Thank you! Your review has been submitted.')
                return redirect(url)
            
def load_product_object(request):
    product_url = 'https://dummyjson.com/products'
    response = requests.get(url=product_url)
    api_data = response.json()
    product_data = api_data.get('product',[])

    for item in product_data:
        title = item.get('title')
        slug = slugify(title)
        description = item.get('description')
        price = int(float(item.get('price', 0)))
        stock = item.get('stock', 0)
        thumbnail_url = item.get('thumbnail')
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
        if thumbnail_url:
            img_response = requests.get(thumbnail_url)
            if img_response.status_code == 200:
                image_name = os.path.basename(urlparse(thumbnail_url).path)
                image_file = ContentFile(img_response.content, name=image_name)

        product = Product.objects.create(
            product_name=title,
            slug=slug,
            description=description,
            price=price,
            stock=stock,
            is_available=(stock > 0),
            category=category_obj
        )

         # প্রোডাক্ট ইমেজ সেভ (thumbnail)
        if image_file:
            product.images.save(image_name, image_file)
            product.save()

        # ProductGallery Image সেভ করা
        for img_url in image_urls:
            try:
                img_res = requests.get(img_url)
                if img_res.status_code == 200:
                    img_name = os.path.basename(urlparse(img_url).path)
                    img_file = ContentFile(img_res.content, name=img_name)
                    ProductGallery.objects.create(product=product, image=img_file)
            except:
                continue
        print("All Api Product is Loaded!!!!!")
        return redirect()
