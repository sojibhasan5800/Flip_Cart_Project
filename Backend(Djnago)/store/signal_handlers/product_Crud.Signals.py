from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from ..models import Product

from ..tasks import sync_product_everywhere, remove_product_everywhere


@receiver(post_save, sender=Product)
def product_saved(sender, instance, **kwargs):
    """
    ✔ Create
    ✔ Update
    ✔ Stock change
    ✔ is_available change

    → Single entry point
    """
    sync_product_everywhere.delay(instance.id,instance.organization.schema_name)


@receiver(post_delete, sender=Product)
def product_deleted(sender, instance, **kwargs):
    """
    ✔ Hard delete cleanup
    """
    remove_product_everywhere.delay(instance.id)
    
