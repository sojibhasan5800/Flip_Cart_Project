# store/tasks.py
import json
import logging

from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Avg, Count, FloatField, IntegerField, Prefetch
from django_redis import get_redis_connection
from redis import Redis
from redis.lock import Lock
from redis.exceptions import LockError,ConnectionError


from store.utils import get_reviews_page
# from ..documents import ProductFeedDocument, ProductSearchDocument
from ..models import Product, ProductGallery, Variation
from django_tenants.utils import schema_context
from ..serializers import ProductDetailSerializer
from django_elasticsearch_dsl.registries import registry

logger = get_task_logger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception, LockError),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
    rate_limit='10/m',           # প্রতি মিনিটে সর্বোচ্চ ১০টা task
)
def sync_product_everywhere(self, product_id: int,schema_name):
    """
    Industry-grade product sync task
    - Redis distributed lock → no race conditions
    - Atomic Redis pipeline
    - Safe JSON serialization
    - Graceful ES offline handling
    """
    redis_client = None
    # Redis connection নেওয়ার সময় try-except
    try:
        redis_client = get_redis_connection("default")
    except ConnectionError as conn_err:
        logger.warning(
            f"Redis unavailable for product {product_id} - retrying ({self.request.retries}/3)",
            extra={"task_id": self.request.id}
        )
        raise self.retry(exc=conn_err, countdown=10)  # ১০ সেকেন্ড পর retry

    except Exception as conn_err:
        logger.error(
            f"Unexpected error connecting to Redis for product {product_id}",
            exc_info=True,
            extra={"task_id": self.request.id}
        )
        # Redis ছাড়া sync সম্ভব না → task fail করে দাও (no retry)
        raise

    # Redis connection সফল হলে lock + sync চালু
    lock_key = f"sync:product:{product_id}"
    

    with Lock(redis_client, lock_key, timeout=90, blocking_timeout=15) as lock:
        try:
            logger.info(f"Starting sync for product {product_id} (task_id: {self.request.id})")
            with schema_context(schema_name):

                product = (
                    Product.objects
                    .select_related('organization', 'category')
                    .prefetch_related(
                        Prefetch(
                            'variation_set',
                            queryset=Variation.objects.filter(is_active=True).only(
                                'id', 'variation_category', 'variation_value'
                            )
                        ),
                        Prefetch(
                            'productgallery_set',
                            queryset=ProductGallery.objects.only('id', 'images')
                        )
                    )
                    .annotate(
                        average_rating=Avg('reviewrating__rating', output_field=FloatField()),  # 🔹 specify FloatField
                        gallery_count=Count('productgallery', output_field=IntegerField()) 
                    )
                    .only(
                        'id', 'product_name', 'slug', 'price', 'mrp', 'images',
                        'stock', 'is_available', 'description', 'created_date',
                        'category__id', 'category__category_name',
                        'organization__id', 'organization__username',
                        'organization__business_name', 'organization__store_logo',
                        # 'organization__store_url'
                    )
                    .get(id=product_id)
                )

            # Elasticsearch sync (conditional)
            # if not getattr(settings, 'ELASTICSEARCH_OFFLINE', True):
            #     try:
            #         _sync_product_to_elasticsearch(product)
            #     except Exception as es_err:
            #         logger.error(
            #             f"ES sync failed for product {product_id}",
            #             exc_info=True,
            #             extra={"task_id": self.request.id}
            #         )
                    # Continue — Redis sync must happen

            # Redis sync — atomic
                _sync_product_to_redis(redis_client, product)

            logger.info(f"Product {product_id} synced successfully")

        except Product.DoesNotExist:
            logger.warning(f"Product {product_id} not found — cleaning up cache")
            _remove_product_from_redis(redis_client, {"id": product_id, "organization_id": None})

        except LockError:
            logger.warning(f"Lock contention for product {product_id} — retrying")
            raise self.retry(countdown=5)  # ৫ সেকেন্ড পর retry

        except Exception as exc:
            logger.error(
                f"Critical sync failure for product {product_id}",
                exc_info=True,
                extra={"task_id": self.request.id}
            )
            raise self.retry(exc=exc)


# def _sync_product_to_elasticsearch(product: Product):
#     """Update relevant ES indices"""
#     for doc_class in registry.get_documents(models=[Product]):
#         try:
#             # partial update if possible
#             doc_class().update(product, action='index', refresh='wait_for')
#             logger.debug(f"ES index '{doc_class.Index.name}' updated for {product.id}")
#         except Exception as e:
#             logger.error(f"ES update failed for index '{doc_class.Index.name}': {e}")


def _sync_product_to_redis(redis_client: Redis, product: Product):
    """Atomic Redis update with pipeline + safe serialization"""
    if not product.is_available or not product.organization_id:
        _remove_product_from_redis(redis_client, product)
        return

    encoder_cls  = DjangoJSONEncoder

    home_data = {
        "id": product.id,
        "organization_id": product.organization_id,
        "product_name": product.product_name,
        "price": float(product.price),
        "average_rating": float(product.average_rating or 0),
        "image": product.images,
        "created_date": product.created_date.isoformat() if product.created_date else None,
    }

     # 🔹 NEW: get first page reviews
    reviews, next_cursor = get_reviews_page(product.id, limit=20)
    detail_data = ProductDetailSerializer(
        product,
        context={"reviews": reviews}
    ).data

    org_id = product.organization_id
    product_id = product.id
    created_ts = int(product.created_date.timestamp()) if product.created_date else 0

    pipe = redis_client.pipeline(transaction=True)

    # Tenant caches
    tenant_latest = f"tenant:{org_id}:latest_products"
    tenant_hash = f"tenant:{org_id}:product:data"
    tenant_detail = f"tenant:{org_id}:product_details:data"

    pipe.zadd(tenant_latest, {product_id: -created_ts})
    pipe.zremrangebyrank(tenant_latest, 1000, -1)
    pipe.hset(tenant_hash, product_id, json.dumps(home_data, cls=encoder_cls))
    pipe.hset(tenant_detail, product_id, json.dumps(detail_data, cls=encoder_cls))

    # Global caches
    global_member = f"{org_id}:{product_id}"
    global_latest = "global:latest_products"
    global_hash = "global:product:data"
    global_detail = "global:product_details:data"

    pipe.zadd(global_latest, {global_member: -created_ts})
    pipe.zremrangebyrank(global_latest, 5000, -1)
    pipe.hset(global_hash, global_member, json.dumps(home_data, cls=encoder_cls))
    pipe.hset(global_detail, global_member, json.dumps(detail_data, cls=encoder_cls))

    pipe.execute()

    logger.debug(f"Redis atomic update done for product {product_id}")


def _remove_product_from_redis(redis_client: Redis, product):
    """Remove from all cache layers"""
    org_id = getattr(product, 'organization_id', None)
    product_id = getattr(product, 'id', product) if isinstance(product, dict) else product

    if not org_id:
        return

    pipe = redis_client.pipeline(transaction=True)

    pipe.zrem(f"tenant:{org_id}:latest_products", product_id)
    pipe.hdel(f"tenant:{org_id}:product:data", product_id)
    pipe.hdel(f"tenant:{org_id}:product_details:data", product_id)

    member_key = f"{org_id}:{product_id}"
    pipe.zrem("global:latest_products", member_key)
    pipe.hdel("global:product:data", member_key)
    pipe.hdel("global:product_details:data", member_key)

    pipe.execute()

    logger.info(f"Product {product_id} removed from all Redis caches")


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def remove_product_everywhere(self, product_id: int):
    """Cleanup when product is deleted"""
    redis_client = get_redis_connection("default")

    try:
        product = Product.objects.select_related('organization').filter(id=product_id).first()

        # Redis cleanup
        _remove_product_from_redis(redis_client, product or {"id": product_id, "organization_id": None})

        # ES cleanup (conditional)
        if not getattr(settings, 'ELASTICSEARCH_OFFLINE', True):
            for doc in registry.get_documents(models=[Product]):
                try:
                    doc().delete(id=product_id)
                except Exception as e:
                    logger.error(f"ES delete failed for {product_id}: {e}")

        logger.info(f"Product {product_id} fully removed from cache & index")

    except Exception as exc:
        logger.error(f"Remove task failed for {product_id}", exc_info=True)
        raise self.retry(exc=exc)