# store/utils.py
from django_redis import get_redis_connection
from .models import ReviewRating
import json

def get_reviews_page(product_id, limit=20, cursor=None, redis_key=None):
    """
    Cursor-based review fetch from Redis
    """
    redis_client = get_redis_connection("default")
    key = redis_key or f"product:{product_id}:reviews"

    if cursor:
        review_ids = redis_client.zrevrangebyscore(key, max=cursor, min="-inf", start=0, num=limit)
    else:
        review_ids = redis_client.zrevrange(key, 0, limit-1)

    review_ids = [int(rid) for rid in review_ids]

    # Fetch only required reviews from DB
    reviews_qs = ReviewRating.objects.filter(id__in=review_ids).select_related('user').order_by('-created_at')

    reviews = []
    for r in reviews_qs:
        full_name = f"{getattr(r.user, 'first_name', '')} {getattr(r.user, 'last_name', '')}".strip() or "Anonymous"
        reviews.append({
            "full_name": full_name,
            "rating": r.rating,
            "subject": r.subject,
            "review": r.review,
            "updated_at": r.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        })

    next_cursor = reviews[-1]['updated_at'] if reviews else None
    return reviews, next_cursor