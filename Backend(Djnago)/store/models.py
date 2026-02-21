from django.db import models
from django.urls import reverse
from django.db.models import Avg, Count
from django.conf import settings
from django_redis import get_redis_connection
import json
from django.utils.text import slugify

from django.db.models import F, Value, CharField
from django.db.models.functions import Concat
# from merchant_user.context import OrganizationContext, get_organization_aware_manager



# Create your models here.

class Product(models.Model):
    product_name    = models.CharField(max_length=200)
    slug            = models.SlugField(max_length=200)
    description     = models.TextField(max_length=500, blank=True)
    price           = models.IntegerField()
    mrp             = models.IntegerField(null=True, blank=True, help_text="Maximum Retail Price")
    images          = models.URLField(max_length=1000, blank=True, null=True, help_text="ImageKit hosted product image URL")
    stock           = models.IntegerField(default=1)
    is_available    = models.BooleanField(default=True)
    category        = models.ForeignKey("category.Category", on_delete=models.CASCADE)
    # Tenant isolation
    organization  = models.ForeignKey("merchant_user.Organization", on_delete=models.SET_NULL,null=True, related_name='products')
    #  NEW: Add delivery tenant link for delivery system
    # delivery_tenant = models.ForeignKey(
    #     "delivery_system.DeliveryTenant", 
    #     on_delete=models.SET_NULL, 
    #     related_name='products',
    #     null=True, 
    #     blank=True
    # )
    
    created_date    = models.DateTimeField(auto_now_add=True)
    modified_date   = models.DateTimeField(auto_now=True)
    # objects = get_organization_aware_manager(models.Manager)()
    class Meta:
        unique_together = ['organization', 'slug']  # Slug unique per tenant
        indexes = [
            # 1. Tenant + availability → most frequent
            models.Index(fields=['organization', 'is_available', 'price']),

            # 2. Tenant + category → category listing
            models.Index(fields=['organization', 'category']),

            # 3. Delivery tenant + availability
            # models.Index(fields=['delivery_tenant', 'is_available', 'price']),

            # 4. Delivery tenant + category
            # models.Index(fields=['delivery_tenant', 'category']),

            # 5. Latest products → sort by created_date
            models.Index(fields=['organization', '-created_date']),

            # 6. Price-only queries → low cost, fast range search
            models.Index(fields=['price']),
        ]

    def save(self, *args, **kwargs):
    # if stock 0 then is_available False 
        # Auto-set delivery_tenant from organization
        # if self.organization and self.organization.delivery_tenant and not self.delivery_tenant:
        #     self.delivery_tenant = self.organization.
        if not self.slug:
            base_slug = slugify(self.product_name)
            slug = base_slug
            counter = 1

            while Product.objects.filter(
                organization=self.organization,
                slug=slug
                ).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            print(f"Generated slug: {slug} for product: {self.product_name}")
            self.slug = slug

        if self.stock == 0:
            self.is_available = False
        super(Product, self).save(*args, **kwargs)

    def get_url(self):
        return reverse('product_detail', args=[self.category.slug, self.slug])

    def __str__(self):
        return self.product_name

    def averageReview(self):
        reviews = ReviewRating.objects.filter(product=self, status=True).aggregate(average=Avg('rating'))
        avg = 0
        if reviews['average'] is not None:
            avg = float(reviews['average'])
        return avg

    def countReview(self):
        reviews = ReviewRating.objects.filter(product=self, status=True).aggregate(count=Count('id'))
        count = 0
        if reviews['count'] is not None:
            count = int(reviews['count'])
        return count

class VariationManager(models.Manager):
    def colors(self):
        return super(VariationManager, self).filter(variation_category='color', is_active=True)

    def sizes(self):
        return super(VariationManager, self).filter(variation_category='size', is_active=True)

variation_category_choice = (
    ('color', 'color'),
    ('size', 'size'),
)

class Variation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variation_category = models.CharField(max_length=100, choices=variation_category_choice)
    variation_value     = models.CharField(max_length=100)
    is_active           = models.BooleanField(default=True)
    created_date        = models.DateTimeField(auto_now=True)

    objects = VariationManager()

    def __str__(self):
        return self.variation_value


class ReviewRating(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    # user = models.ForeignKey("accounts.Account", on_delete=models.CASCADE)
    user = models.ForeignKey("accounts.Account", on_delete=models.DO_NOTHING, null=True, blank=True)
    subject = models.CharField(max_length=100, blank=True)
    review = models.TextField(max_length=500, blank=True)
    rating = models.FloatField()
    ip = models.CharField(max_length=20, blank=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.subject
    class Meta:
        ordering = ['-rating', '-updated_at']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update Redis cache on every save
        cache = get_redis_connection("default")

        # Annotate database query to get full_name from first_name + last_name

        reviews_qs = list(self.product.reviewrating_set.annotate(
            full_name=Concat(F('user__first_name'), Value(' '), F('user__last_name'), output_field=CharField())
        ).values(
            'full_name', 'rating', 'subject', 'review', 'updated_at'
        ).order_by('-rating', '-updated_at'))

        reviews = []
        for r in reviews_qs:
            reviews.append({
                'full_name': r['full_name'],
                'rating': r['rating'],
                'subject': r['subject'],
                'review': r['review'],
                # Convert datetime to string
                'updated_at': r['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
            })

        cache.set(f'product_reviews:{self.product.id}', json.dumps(reviews), ex=3600)


class ProductGallery(models.Model):
    product = models.ForeignKey(Product, default=None, on_delete=models.CASCADE)
    images          = models.URLField(max_length=1000, blank=True, null=True, help_text="ImageKit hosted product image URL") 

    def __str__(self):
        return self.product.product_name

    class Meta:
        verbose_name = 'productgallery'
        verbose_name_plural = 'product gallery'

 