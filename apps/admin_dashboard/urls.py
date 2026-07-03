from .views import *
from rest_framework import routers
from django.urls import path, include
from .views import UserStatisticsView

router = routers.DefaultRouter()

#------------------------Category URLs------------------------
router.register(r'eating-style', EatingStyleViewSet)
router.register(r'allergies', AllergyViewSet)
router.register(r'medical-conditions', MedicalConditionViewSet)
router.register(r'avatars', AvatarViewSet)

#-----------------------Feedback URLs------------------------
router.register(r'support', FeedbackViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path("privacy-policy/", PrivacyPolicyAPIView.as_view()),
    path("terms/", TermsAndConditionsAPIView.as_view()),
    path("about-us/", AboutUsAPIView.as_view()),
    path("user-statistics/", UserStatisticsView.as_view()),
]