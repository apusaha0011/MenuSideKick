from django.contrib import admin
from .models import (
    PrivacyPolicyModel,
    TermsAndConditionsModel,
    AboutUsModel,
    EatingStyleModel,
    AllergyModel,
    MedicalConditionModel,
    AvatarModel,
    FeedbackModel
)

# Register your models here.
admin.site.register(PrivacyPolicyModel)
admin.site.register(TermsAndConditionsModel)
admin.site.register(AboutUsModel)
admin.site.register(EatingStyleModel)
admin.site.register(AllergyModel)
admin.site.register(MedicalConditionModel)
admin.site.register(AvatarModel)
admin.site.register(FeedbackModel)