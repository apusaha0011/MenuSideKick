from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class OTPBackend(BaseBackend):
    def authenticate(self, request, email=None, otp=None):
        from .models import EmailOTP
        if email and otp:
            try:
                email_otp = EmailOTP.objects.get(email=email, otp=otp, is_used=False)
                if email_otp.is_valid():
                    email_otp.is_used = True
                    email_otp.save()
                    user, _ = User.objects.get_or_create(email=email)
                    return user
            except EmailOTP.DoesNotExist:
                return None
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
