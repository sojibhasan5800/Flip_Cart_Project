# # store/documents.py
# store/documents.py (Updated with more fields for full product data in ES)
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from .models import Product
from merchant_user.models import Organization
from category.models import Category
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@registry.register_document
class ProductFeedDocument(Document):
    organization_id = fields.IntegerField(attr='organization.id')
    average_rating = fields.FloatField(attr='average_rating')

    class Index:
        name = 'products_feed'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0,
        }

    class Django:
        model = Product
        fields = [
            'id',
            'product_name',
            'price',
            'images',
            'created_date',
            'is_available'
        ]
    

@registry.register_document
class ProductSearchDocument(Document):
    product_name = fields.TextField(
        analyzer="standard",
        fields={"raw": fields.KeywordField()}
    )
    description = fields.TextField(analyzer="standard")

    organization_id = fields.IntegerField(attr='organization.id')

    class Index:
        name = 'products_search'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0,
        }

    class Django:
        model = Product
        fields = [
            'id',
            # 'product_name',
            # 'description',
        ]


# ✅ 4️⃣ Feed click → Seller vs Global (Tracking)

# Frontend যখন click করবে, পাঠাবে:

# {
#   "product_id": 12,
#   "source": "seller"   // or "global"
# }

# Backend logic:

# if source == "seller":
#     key = f"tenant:{org_id}:product_details:data"
# else:
#     key = "global:product_details:data"










#     def update(self, *args, **kwargs):
#         if getattr(settings, 'ELASTICSEARCH_OFFLINE', False):
#             logging.warning("Elasticsearch update skipped (offline mode).")
#             return
#         return super().update(*args, **kwargs)

#     def delete(self, *args, **kwargs):
#         if getattr(settings, 'ELASTICSEARCH_OFFLINE', False):
#             logging.warning("Elasticsearch delete skipped (offline mode).")
#             return
#         return super().delete(*args, **kwargs)

     
