from .models import Product
from django_elasticsearch_dsl.registries import registry
from django_elasticsearch_dsl import Document,Index,fields

@registry.register_document
class ProductDocument(Document):
    class Index:
        name = 'products'
        settings={
            'number_of_shards': 1,
            'number_of_replicas': 0,
        }

    class Django:
        model = Product
        fields= {
            'id',
            'product_name',
            'description',
            'price'
        }