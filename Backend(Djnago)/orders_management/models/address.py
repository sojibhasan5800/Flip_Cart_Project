from django.db import models
from django.conf import settings


class ShippingAddress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='shipping_addresses'
    )

    name = models.CharField(max_length=150)
    email = models.EmailField()

    street = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)

    zip = models.CharField(max_length=20)
    country = models.CharField(max_length=100)

    phone = models.CharField(max_length=30)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.city}"