from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, 
    ProfileViewSet, 
    GoogleLoginView, 
    AppleLoginView, 
    RequestOTPView, 
    LogoutView, 
    VerifyOTPView
)
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'profiles', ProfileViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('auth/request-otp/', RequestOTPView.as_view(), name='request-otp'),
    path('auth/verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('auth/google/', GoogleLoginView.as_view(), name='google_login_new'),
    path('auth/apple/', AppleLoginView.as_view(), name='apple_login'),
]   