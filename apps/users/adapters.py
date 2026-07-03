from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model

class CustomAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return True


User = get_user_model()

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        This is called **before** allauth creates a new user.
        We'll link to existing user if email exists.
        """
        # If social account already exists, do nothing
        if sociallogin.is_existing:
            return

        email = sociallogin.account.extra_data.get('email')
        if not email:
            return

        try:
            # Check if user with this email already exists
            user = User.objects.get(email=email)
            # Link this social account to the existing user
            sociallogin.connect(request, user)
        except User.DoesNotExist:
            # No user exists → will create new user as usual
            pass

    def is_open_for_signup(self, request, sociallogin):
        # Always allow signup
        return True
