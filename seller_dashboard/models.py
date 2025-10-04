# seller_dashboard/models.py
from django.db import models
from accounts.models import Account
from store.models import Product
from orders.models import Order, OrderProduct

class SellerAnalytics(models.Model):
    seller = models.ForeignKey(Account, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    total_orders = models.IntegerField(default=0)
    total_revenue = models.FloatField(default=0.0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.seller.email} - {self.product.product_name}"
