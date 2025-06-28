from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import Product, ProductGallery
import cloudinary.uploader


@receiver(post_delete, sender=Product)
def delete_product_image_cloudinary(sender, instance, **kwargs):
    if instance.images:
        try:
            cloudinary.uploader.destroy(instance.images.public_id)
        except:
            pass


@receiver(post_delete, sender=ProductGallery)
def delete_gallery_image_cloudinary(sender, instance, **kwargs):
    if instance.image:
        try:
            cloudinary.uploader.destroy(instance.image.public_id)
        except:
            pass
