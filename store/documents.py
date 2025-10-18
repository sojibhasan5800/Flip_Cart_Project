# store/documents.py
from .models import Product
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from django.conf import settings
import logging

@registry.register_document
class ProductDocument(Document):
    class Index:
        name = 'products'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0,
        }

    class Django:
        model = Product
        fields = [
            'id',
            'product_name',
            'description',
            'price',  # Elasticsearch automatically maps numeric type
        ]

    def update(self, *args, **kwargs):
        if getattr(settings, 'ELASTICSEARCH_OFFLINE', False):
            logging.warning("Elasticsearch update skipped (offline mode).")
            return
        return super().update(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if getattr(settings, 'ELASTICSEARCH_OFFLINE', False):
            logging.warning("Elasticsearch delete skipped (offline mode).")
            return
        return super().delete(*args, **kwargs)

     
