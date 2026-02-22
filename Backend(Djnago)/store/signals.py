from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Product,ReviewRating
from django_redis import get_redis_connection
from django_tenants.utils import schema_context
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
    sync_product_everywhere.delay(instance.id,instance.organization.schema_name)


@receiver(post_delete, sender=Product)
def product_deleted(sender, instance, **kwargs):
    """
    ✔ Hard delete cleanup
    """
    remove_product_everywhere.delay(instance.id)
    

@receiver(post_save, sender=ReviewRating)
def update_review_redis_on_save(sender, instance, **kwargs):
    """
    🔹 Whenever a ReviewRating is saved, update Redis ZSET for the product
       in the correct tenant schema
    """
    schema_name = instance.product.organization.schema_name if instance.product.organization else "public"
    with schema_context(schema_name):
        redis_client = get_redis_connection("default")
        key = f"{schema_name}:product:{instance.product.id}:reviews"

        # Use created_at timestamp as score for cursor-based pagination
        redis_client.zadd(key, {instance.id: instance.created_at.timestamp()})
        redis_client.expire(key, 3600)  # TTL 1 hour


@receiver(post_delete, sender=ReviewRating)
def remove_review_from_redis_on_delete(sender, instance, **kwargs):
    """
    🔹 Whenever a ReviewRating is deleted, remove it from Redis ZSET
       in the correct tenant schema
    """
    schema_name = instance.product.organization.schema_name if instance.product.organization else "public"
    with schema_context(schema_name):
        redis_client = get_redis_connection("default")
        key = f"{schema_name}:product:{instance.product.id}:reviews"
        redis_client.zrem(key, instance.id)
