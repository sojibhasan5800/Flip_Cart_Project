from django.db import models


class PaymentAnalytics(models.Model):

    transaction_id = models.CharField(
        max_length=255,
        db_index=True
    )

    payment_type = models.CharField(
        max_length=50
    )

    gateway = models.CharField(
        max_length=50
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    currency = models.CharField(
        max_length=10,
        default='BDT'
    )

    status = models.CharField(
        max_length=20
    )

    metadata = models.JSONField(
        default=dict,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        ordering = ['-created_at']

        indexes = [
            models.Index(fields=['gateway']),
            models.Index(fields=['payment_type']),
            models.Index(fields=['status']),
        ]

    def __str__(self):

        return (
            f"{self.payment_type} - "
            f"{self.amount}"
        )