from rest_framework import serializers
from .models import TransactionModel, PaymentPlan


class PaymentPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentPlan
        fields = ['id', 'name', 'price', 'currency', 'interval', 'is_active', 'apple_product_id', 'google_product_id']


class IAPValidateSerializer(serializers.Serializer):
    platform = serializers.ChoiceField(choices=['apple', 'google'])
    product_id = serializers.CharField()
    purchase_token = serializers.CharField()
    transaction_id = serializers.CharField()


class SubscriptionStatusSerializer(serializers.Serializer):
    status = serializers.CharField()
    start_date = serializers.DateTimeField(required=False)
    renewal_date = serializers.DateTimeField()
    plan_name = serializers.CharField()


class CheckSubscriptionSerializer(serializers.Serializer):
    active = serializers.BooleanField()
    need_subscription = serializers.BooleanField()
    status = serializers.CharField()
    plan = serializers.CharField()
    renewal_date = serializers.DateTimeField()

