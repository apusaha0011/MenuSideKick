from django.contrib import admin
from .models import (
    PaymentPlan,
    TransactionModel
)

# Register your models here.
admin.site.register(PaymentPlan)
admin.site.register(TransactionModel)
