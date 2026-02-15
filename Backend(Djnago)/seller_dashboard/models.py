# from django.db import models
# from django.contrib.auth import get_user_model
# from django.utils import timezone

# User = get_user_model()

# class SellerAnalytics(models.Model):
#     seller = models.ForeignKey(User, on_delete=models.DO_NOTHING,null=True, related_name='analytics')
#     # total_sales = models.FloatField(default=0)
#     total_sales = models.IntegerField(default=0)
#     total_orders = models.IntegerField(default=0)
#     total_items_sold = models.IntegerField(default=0)
#     top_products = models.JSONField(null=True, blank=True)      
#     inventory_summary = models.JSONField(null=True, blank=True)     
#     last_updated = models.DateTimeField(auto_now=True)
#     class Meta:
#         unique_together = (('seller',),)

#     def __str__(self):
#         return f"{self.seller.email} Analytics"
