from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Product
from .tasks import sync_product_everywhere, remove_product_everywhere


@receiver(post_save, sender=Product)
def product_saved(sender, instance, **kwargs):
    """
    ✔ Create
    ✔ Update
    ✔ Stock change
    ✔ is_available change

    → Single entry point
    """
    sync_product_everywhere.delay(instance.id)


@receiver(post_delete, sender=Product)
def product_deleted(sender, instance, **kwargs):
    """
    ✔ Hard delete cleanup
    """
    remove_product_everywhere.delay(instance.id)
    



# # store/signals.py
# from django.db.models.signals import post_delete, post_save
# from django.dispatch import receiver
# from .models import Product, ProductGallery
# import cloudinary.uploader
# from django.conf import settings
# import logging

# # ----------------------------
# # Cloudinary image deletion
# # ----------------------------
# @receiver(post_delete, sender=Product)
# def delete_product_image_cloudinary(sender, instance, **kwargs):
#     if instance.images:
#         try:
#             cloudinary.uploader.destroy(instance.images.public_id)
#         except:
#             pass

# @receiver(post_delete, sender=ProductGallery)
# def delete_gallery_image_cloudinary(sender, instance, **kwargs):
#     if instance.image:
#         try:
#             cloudinary.uploader.destroy(instance.image.public_id)
#         except:
#             pass

# # ----------------------------
# # Elasticsearch update/delete handler
# # ----------------------------
# @receiver(post_save, sender=Product)
# def update_product_elasticsearch(sender, instance, **kwargs):
#     if getattr(settings, 'ELASTICSEARCH_OFFLINE', False):
#         return  # Skip if offline
#     try:
#         from .documents import ProductDocument  # lazy import here
#         ProductDocument().update(instance)
#     except Exception as e:
#         import logging
#         logging.warning(f"Elasticsearch update skipped: {e}")

# @receiver(post_delete, sender=Product)
# def delete_product_elasticsearch(sender, instance, **kwargs):
#     if getattr(settings, 'ELASTICSEARCH_OFFLINE', False):
#         return  # Skip if offline
#     try:
#         from .documents import ProductDocument  # lazy import here
#         ProductDocument().update(instance, action="delete")
#     except Exception as e:
#         import logging
#         logging.warning(f"Elasticsearch delete skipped: {e}")

