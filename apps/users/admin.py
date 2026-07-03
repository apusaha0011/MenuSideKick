from django.contrib import admin
from .models import (
    CustomUserModel,
    ProfileModel,
    ProfileEatingStyle,
    EmailOTPModel,
)

# Register your models here.
admin.site.register(CustomUserModel)
admin.site.register(ProfileModel)
admin.site.register(ProfileEatingStyle)
admin.site.register(EmailOTPModel)  