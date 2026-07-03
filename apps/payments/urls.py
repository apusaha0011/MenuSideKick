from django.urls import path, include
from .views import (
    PaymentPlanViewSet,
    SubscriptionManageView, 
    IAPValidateView, 
    CheckSubscriptionView
)
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'payment/plans', PaymentPlanViewSet, basename='payment-plans')

urlpatterns = [
    path('', include(router.urls)),
    path('payment/subscription/manage/', SubscriptionManageView.as_view(), name='subscription_manage'),
    path('payment/iap/validate/', IAPValidateView.as_view(), name='iap_validate'),
    path('payment/check-subscription/', CheckSubscriptionView.as_view(), name='check_subscription'),
]
