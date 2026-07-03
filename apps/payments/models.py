from django.db import models
from django.conf import settings


# models
class PaymentPlan(models.Model):
    INTERVAL_CHOICES = [
        ('trial', 'Trial'),
        ('Week', 'Week'),
        ('month', 'Month'),
        ('year', 'Year'),
    ]
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')
    interval = models.CharField(max_length=20, choices=INTERVAL_CHOICES)
    is_active = models.BooleanField(default=True)
    apple_product_id = models.CharField(max_length=255, null=True, blank=True)
    google_product_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name




class TransactionModel(models.Model):
    PLATFORM_CHOICES = [
        ('google', 'Google Play'),
        ('apple', 'Apple App Store'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES)
    product_id = models.CharField(max_length=255)  # e.g. "premium_monthly"
    purchase_token = models.TextField(null=True, blank=True)            # token/receipt from mobile
    status = models.CharField(max_length=50)       # active, expired, refunded, etc.
    purchased_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} - {self.product_id} ({self.platform})"
