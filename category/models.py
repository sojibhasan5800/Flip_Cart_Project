from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
User = get_user_model()

# Create your models here.
def get_default_admin_user():
    """Return default admin user if exists"""
    try:
        return User.objects.get(email="admin@gmail.com").id
    except ObjectDoesNotExist:
        return None
    

class Category(models.Model):
    category_name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    url = models.URLField(max_length=250,blank=True)
    description = models.TextField(max_length=255, blank=True)
    cat_image = models.ImageField(upload_to='photos/categories', blank=True)

    account = models.ForeignKey(User, on_delete=models.CASCADE, default= get_default_admin_user,null=True,blank=True)


    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def get_url(self):
            return reverse('products_by_category', args=[self.slug])

    def __str__(self):
        return self.category_name
