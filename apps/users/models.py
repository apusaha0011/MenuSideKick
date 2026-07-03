from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from datetime import timedelta
from apps.admin_dashboard.models import EatingStyleModel, AllergyModel, MedicalConditionModel, AvatarModel


# ---------------------------- Custom User Manager ----------------------------

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)

        if password:
            user.set_password(password)  # hash it properly
        else:
            user.set_unusable_password()  # prevents login with empty password

        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if not password:
            raise ValueError("Superuser must have a password.")

        return self.create_user(email, password, **extra_fields)
    

# ---------------------------- Custom User Model ----------------------------


class CustomUserModel(AbstractBaseUser, PermissionsMixin):
    class Meta:
        app_label = 'users'
        swappable = 'AUTH_USER_MODEL'

    CURRENT_PLAN_CHIOICES = [
        ('free', 'free'),
        ('monthly', 'monthly'),
        ('yearly', 'yearly'),
    ]

    LanguageChoices = [
        ('English', 'English'),
        ('Spanish', 'Spanish'),
        ('French', 'French'),
        ('Bangla', 'Bangla'),
    ]

    
    email = models.EmailField(unique=True)
    country = models.CharField(max_length=255, blank=True, null=True)
    language = models.CharField(choices=LanguageChoices, default='English', max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    is_blocked = models.BooleanField(default=False)
    
    paid_user = models.BooleanField(default=False)
    current_plan = models.CharField(max_length=20, choices=CURRENT_PLAN_CHIOICES, default='free')
    current_period_start = models.DateTimeField(blank=True, null=True)
    current_period_end = models.DateTimeField(blank=True, null=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


# ---------------------------- Profile Model ----------------------------

class ProfileModel(models.Model):

    # personal info
    user = models.ForeignKey(CustomUserModel, on_delete=models.CASCADE, related_name='profiles')
    profile_name = models.CharField(max_length=150)
    profile_image = models.ImageField(upload_to='profiles/', max_length=2048, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)
    avatar = models.URLField(max_length=2048, blank=True, null=True)
    
    # category/food preference fields
    # Use a through model so each (profile, eating_style) can have its own level
    eating_style = models.ManyToManyField('admin_dashboard.EatingStyleModel',blank=True,related_name='profiles',through='ProfileEatingStyle')
    allergies = models.ManyToManyField('admin_dashboard.AllergyModel', blank=True, related_name='profiles')
    medical_conditions = models.ManyToManyField('admin_dashboard.MedicalConditionModel', blank=True, related_name='profiles')
    magic_list = models.JSONField(default=list, blank=True)

    my_platters = models.OneToOneField(
        'ai_responses.MyPlateModel', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='profile_platter'
    )

    # profile state
    is_active = models.BooleanField(default=True)

    class Meta:
        # Ensure unique profile name per user
        constraints = [
            models.UniqueConstraint(fields=['user', 'profile_name'], name='unique_profile_per_user')
        ]

    def save(self, *args, **kwargs):
        """
        When a profile is set to active=True,
        automatically deactivate all other profiles for this user.
        """
        if self.is_active:
            # Deactivate other profiles of the same user
            ProfileModel.objects.filter(user=self.user, is_active=True).exclude(pk=self.pk).update(is_active=False)
        
        # Mutual exclusivity logic
        if self.profile_image and self.avatar:
            # If both are present, prioritize the one that might have been recently set.
            # However, typical usage is one or the other from frontend.
            # If both exist, we assume profile_image was just uploaded or is preferred.
            self.avatar = ""
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email}'s Profile - {self.profile_name}"
    

# Through model to store per-profile eating-style level
class ProfileEatingStyle(models.Model):
    LEVEL_CHOICES = [
        ('Flexible', 'Flexible'),
        ('Balanced', 'Balanced'),
        ('Strict', 'Strict'),
    ]

    profile = models.ForeignKey(ProfileModel, on_delete=models.CASCADE, related_name='eating_style_links')
    eating_style = models.ForeignKey(EatingStyleModel, on_delete=models.CASCADE, related_name='profile_links')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='Balanced')

    class Meta:
        unique_together = ('profile', 'eating_style')

    def __str__(self):
        return f"{self.profile} - {self.eating_style} ({self.level})"
    

# ---------------------------- Email OTP Model ----------------------------
class EmailOTPModel(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"OTP for {self.email} - {'Used' if self.is_used else 'Unused'}"

    def is_valid(self):
        return not self.is_used and (timezone.now() - self.created_at) < timedelta(minutes=5)
    
