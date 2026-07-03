from rest_framework import serializers
from .models import *

# ------------------------Settings Serializers------------------------
class PrivacyPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivacyPolicyModel
        fields = "__all__"

class TermsAndConditionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TermsAndConditionsModel
        fields = "__all__"

class AboutUsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AboutUsModel
        fields = "__all__"

# ------------------------Category Serializers----------------------

class EatingStyleSerializer(serializers.ModelSerializer):
    class Meta:
        model = EatingStyleModel
        fields = "__all__"

        
class AllergySerializer(serializers.ModelSerializer):
    class Meta:
        model = AllergyModel
        fields = "__all__"

class MedicalConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalConditionModel
        fields = "__all__"


class AvatarSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvatarModel
        fields = "__all__"

# ------------------------Feedback Serializers----------------------
class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedbackModel
        fields = "__all__"
