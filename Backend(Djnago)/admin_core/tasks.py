# tasks.py
from celery import shared_task
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache
from django_redis import get_redis_connection

import logging
from .models import Coupon
from datetime import timedelta

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def expire_single_coupon_task(self, coupon_id):
    """
    Task to expire a single coupon at its exact expiry time
    """
    try:
        with transaction.atomic():
            coupon = Coupon.objects.select_for_update().get(id=coupon_id)
            
            # Double-check expiry time
            if timezone.now() >= coupon.valid_to and coupon.is_active:
                coupon.is_active = False
                coupon.is_expired = True
                coupon.celery_task_id = None  # Clear task ID
                coupon.save(update_fields=['is_active', 'is_expired', 'celery_task_id', 'updated_at'])
                
                logger.info(f"Coupon {coupon.code} expired automatically at {timezone.now()}")
                
                # Send notification (optional)
                # send_coupon_expiry_notification(coupon)
                
                return {
                    "coupon_id": str(coupon_id),
                    "code": coupon.code,
                    "expired_at": timezone.now().isoformat(),
                    "status": "expired"
                }
            else:
                logger.info(f"Coupon {coupon.code} not expired yet, skipping...")
                return {"status": "not_expired_yet"}
                
    except Coupon.DoesNotExist:
        logger.error(f"Coupon with id {coupon_id} not found")
    except Exception as e:
        logger.error(f"Failed to expire coupon {coupon_id}: {str(e)}")
        # Retry after 1 minute
        raise self.retry(exc=e, countdown=60)

@shared_task
def bulk_expire_coupons_check():
    """
    Safety net: Check for any coupons that might have been missed
    Runs every 6 hours as backup
    """
    now = timezone.now()
    expired_coupons = Coupon.objects.filter(
        valid_to__lte=now,
        is_active=True,
        is_expired=False
    )
    
    count = 0
    for coupon in expired_coupons:
        coupon.is_active = False
        coupon.is_expired = True
        coupon.save(update_fields=['is_active', 'is_expired', 'updated_at'])
        count += 1
        
        # Cancel any pending task
        if coupon.celery_task_id:
            coupon.cancel_scheduled_task()
    
    if count > 0:
        logger.warning(f"Bulk check expired {count} coupons that were missed")
    
    return {"bulk_expired_count": count}

@shared_task
def cleanup_old_coupons():
    """
    Delete coupons that expired more than 90 days ago
    """
    cutoff_date = timezone.now() - timedelta(days=90)
    
    old_coupons = Coupon.objects.filter(
        valid_to__lt=cutoff_date,
        is_expired=True
    )
    
    deleted_count = old_coupons.count()
    
    # Cancel any remaining tasks before deletion
    for coupon in old_coupons:
        if coupon.celery_task_id:
            coupon.cancel_scheduled_task()
    
    old_coupons.delete()
    
    logger.info(f"Cleaned up {deleted_count} old expired coupons")
    return {"cleaned_up": deleted_count}


class RedisOrgCounter:
    ORG_COUNT_KEY = "active_verified_org_count"

    def __init__(self, redis_alias="default", ttl=3600):
        self.redis_alias = redis_alias
        self.ttl = ttl
        self.redis = get_redis_connection(redis_alias)

    def initialize_count(self):
        """
        প্রথমবার Redis এ set করার জন্য, DB থেকে load
        """
        from merchant_user.models import Organization
        try:
            count = Organization.objects.filter(is_verified=True, is_active=True).count()
            self.redis.set(self.ORG_COUNT_KEY, count, ex=self.ttl)  # TTL 1 hour
            logger.info(f"Org count initialized in Redis: {count}")
            return count
        except Exception as e:
            logger.error(f"Failed to initialize org count: {e}")
            return 0

    def increment(self):
        """
        এক organization approve হলে count +1
        """
        try:
            self.redis.incr(self.ORG_COUNT_KEY)
            logger.info("Org count incremented in Redis")
        except Exception as e:
            logger.error(f"Failed to increment org count: {e}")

    def decrement(self):
        """
        এক organization reject/delete হলে count -1
        """
        try:
            self.redis.decr(self.ORG_COUNT_KEY)
            logger.info("Org count decremented in Redis")
        except Exception as e:
            logger.error(f"Failed to decrement org count: {e}")

    def get_count(self):
        """
        Cached org count fetch
        """
        try:
            count = self.redis.get(self.ORG_COUNT_KEY)
            if count is None:
                return self.initialize_count()
            return int(count)
        except Exception as e:
            logger.error(f"Failed to get org count: {e}")
            return 0

