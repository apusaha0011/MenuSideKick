from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from django.utils import timezone
from datetime import timedelta
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from .serializers import (
    PaymentPlanSerializer, 
    IAPValidateSerializer, 
    SubscriptionStatusSerializer, 
    CheckSubscriptionSerializer
)
from .models import TransactionModel, PaymentPlan
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi







class PaymentPlanViewSet(viewsets.ModelViewSet):
    queryset = PaymentPlan.objects.filter(is_active=True)
    serializer_class = PaymentPlanSerializer
    permission_classes = [IsAuthenticated]




class SubscriptionManageView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SubscriptionStatusSerializer

    @swagger_auto_schema(
        responses={200: SubscriptionStatusSerializer()},
        operation_description="Get current subscription status"
    )
    def get(self, request):
        user = request.user
        return Response({
            "status": "active" if user.paid_user and user.current_period_end > timezone.now() else "inactive",
            "start_date": user.current_period_start,
            "renewal_date": user.current_period_end,
            "plan_name": user.current_plan
        })


class IAPValidateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = IAPValidateSerializer

    @swagger_auto_schema(
        request_body=IAPValidateSerializer,
        responses={200: openapi.Response('Verification successful', schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                "platform": openapi.Schema(type=openapi.TYPE_STRING),
                "product_id": openapi.Schema(type=openapi.TYPE_STRING),
                "purchase_token": openapi.Schema(type=openapi.TYPE_STRING),
                "subscription": openapi.Schema(type=openapi.TYPE_OBJECT)
            }
        ))},
        
        operation_description="Validate an In-App Purchase"
    )
    def post(self, request):
        serializer = IAPValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        platform = data['platform']
        product_id = data['product_id']
        purchase_token = data['purchase_token']
        transaction_id = data['transaction_id']

        # Logic to determine interval and price from product_id or PaymentPlan
        plan = PaymentPlan.objects.filter(
            Q(apple_product_id=product_id) | Q(google_product_id=product_id)
        ).first()

        days = 30
        interval = "month"
        price = "7.99"
        currency = "USD"

        if plan:
            if plan.interval == 'year':
                days = 365
            elif plan.interval == 'Week':
                days = 7
            elif plan.interval == 'trial':
                days = 3
            interval = plan.interval
            price = str(plan.price)
            currency = plan.currency
        elif "annual" in product_id or "year" in product_id:
            days = 365
            interval = "year"
            price = "59.99"
        elif "trial" in product_id:
            days = 3
            interval = "trial"
            price = "0.00"

        expiry = timezone.now() + timedelta(days=days)

        # Update user
        user = request.user
        user.paid_user = True
        user.current_plan = product_id
        user.current_period_start = timezone.now()
        user.current_period_end = expiry
        user.save()

        # Create transaction record
        TransactionModel.objects.create(
            user=user,
            platform=platform,
            product_id=product_id,
            purchase_token=purchase_token,
            status="active",
            expires_at=expiry
        )

        return Response({
            "success": True,
            "platform": platform,
            "product_id": product_id,
            "purchase_token": purchase_token,
            "transaction_id": transaction_id,
            "subscription": {
                "status": "active",
                "plan": product_id,
                "price": price,
                "currency": currency,
                "interval": interval,
                "renewal_date": expiry
            }
        })


class CheckSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CheckSubscriptionSerializer

    @swagger_auto_schema(
        responses={200: CheckSubscriptionSerializer()},
        operation_description="Check if the user has an active subscription"
    )
    def get(self, request):
        user = request.user
        is_active = user.paid_user and user.current_period_end and user.current_period_end > timezone.now()
        
        return Response({
            "active": is_active,
            "need_subscription": not is_active,
            "status": "active" if is_active else "inactive",
            "plan": user.current_plan,
            "renewal_date": user.current_period_end
        })
