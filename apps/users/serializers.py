import json
from rest_framework import serializers
from .models import CustomUserModel, ProfileModel, EmailOTPModel, ProfileEatingStyle
from apps.admin_dashboard.models import EatingStyleModel, AllergyModel, MedicalConditionModel
from .utils import generate_otp, send_otp_via_email
from django.utils import timezone
from datetime import timedelta
from rest_framework_simplejwt.tokens import RefreshToken
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.registration.serializers import SocialLoginSerializer

class SimpleProfileSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=True)
    class Meta:
        model = ProfileModel
        fields = ["id", "profile_name", "is_active", "profile_image", "avatar"]


#----------------------------- User Serializer ----------------------------

class UserSerializer(serializers.ModelSerializer):
    profiles = SimpleProfileSerializer(many=True, required=False)

    class Meta:
        model = CustomUserModel
        fields = '__all__'

    def update(self, instance, validated_data):
        profiles_data = validated_data.pop("profiles", None)

        # update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # update nested profiles
        if profiles_data:
            for profile_data in profiles_data:
                profile_id = profile_data.get("id")
                if not profile_id:
                    raise serializers.ValidationError("Profile ID is required.")

                try:
                    profile = instance.profiles.get(id=profile_id)
                except ProfileModel.DoesNotExist:
                    raise serializers.ValidationError(
                        f"Profile with id {profile_id} does not belong to this user."
                    )

                # update profile fields
                for key, value in profile_data.items():
                    if key != "id":  # never allow modifying the id
                        setattr(profile, key, value)

                profile.save()

        return instance




class CustomRegisterSerializer(RegisterSerializer):
    """Disable username completely; only use email and password"""
    username = None
    # Provide defaults so Swagger UI is pre-filled for quick testing
    email = serializers.EmailField(default='test@example.com')
    password1 = serializers.CharField(default='Password123!', write_only=True)
    password2 = serializers.CharField(default='Password123!', write_only=True)

    def get_cleaned_data(self):
        return {
            'email': self.validated_data.get('email', ''),
            'password1': self.validated_data.get('password1', ''),
            'password2': self.validated_data.get('password2', ''),
        }

#----------------------------- Profile Serializer ----------------------------
# Moving this outside allows drf-yasg to generate a better schema name
class EatingStyleLevelSerializer(serializers.Serializer):
    eating_style_name = serializers.CharField(help_text="Name of the eating style", default="Vegan")
    level = serializers.ChoiceField(
        choices=[('Flexible', 'Flexible'), ('Balanced', 'Balanced'), ('Strict', 'Strict')],
        default='Balanced'
    )

#----------------------------- Profile Serializer ----------------------------
class ProfileSerializer(serializers.ModelSerializer):
    # Explicitly define profile_image as ImageField for Swagger to recognize it
    # This overrides the model field and ensures proper form rendering in Swagger UI
    profile_image = serializers.ImageField(
        required=False,
        allow_null=True,
        help_text="Upload profile image (will be stored in S3). If provided, avatar will be set to null."
    )

    # Eating style nested serializer
    eating_style = EatingStyleLevelSerializer(many=True, required=False)

    # SlugRelatedField for allergies with Swagger examples
    allergies = serializers.SlugRelatedField(
        many=True,
        queryset=AllergyModel.objects.all(),
        slug_field='allergy_name',
        required=False,
        help_text="List of allergy names (e.g., peanut, gluten)"
    )

    # SlugRelatedField for medical conditions with Swagger examples
    medical_conditions = serializers.SlugRelatedField(
        many=True,
        queryset=MedicalConditionModel.objects.all(),
        slug_field='medical_condition_name',
        required=False,
        help_text="List of medical condition names (e.g., diabetes, hypertension)"
    )

    # Magic list field
    magic_list = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=['pizza', 'salad'],  # Pre-filled demo data
        help_text="List of favorite foods"
    )

    # Explicit model-field overrides with defaults shown in schema
    profile_name = serializers.CharField(
        default='Default Profile',
        help_text="Name of the profile"
    )
    country = serializers.CharField(
        default='USA',
        allow_blank=True,
        required=False,
        help_text="Country name"
    )
    avatar = serializers.URLField(
        default='https://example.com/avatar.png',
        allow_blank=True,
        required=False,
        help_text="Avatar URL (will be cleared if profile_image is provided)"
    )
    date_of_birth = serializers.DateField(
        required=False,
        allow_null=True,
        default='1995-01-01',
        help_text="Date of birth in YYYY-MM-DD format"
    )

    # ------------------- Robust Parsing -------------------
    def to_internal_value(self, data):
        """
        Handle cases where array fields might be sent as JSON strings or comma-separated values.
        
        Why: When using multipart/form-data (required for image uploads), 
        clients like Swagger UI or Postman might send array fields in different formats
        (e.g., repeated keys, JSON strings, or CSV). This method normalizes the input.
        """
        # Create a mutable copy of the data
        if hasattr(data, 'dict'):
            new_data = data.copy()
        else:
            new_data = dict(data)

        array_fields = ['magic_list', 'allergies', 'medical_conditions', 'eating_style']
        
        for field in array_fields:
            if field in new_data:
                # Use getlist if it's a QueryDict to get all values for repeated keys
                if hasattr(data, 'getlist'):
                    value = data.getlist(field)
                else:
                    value = new_data.get(field)

                # If it's a single string (not a list yet), try to parse it
                if isinstance(value, str):
                    value = [value] # Wrap in list to use the same logic
                
                if isinstance(value, list):
                    # Special case: single string in a list that might be CSV or JSON
                    if len(value) == 1 and isinstance(value[0], str):
                        s_val = value[0].strip()
                        if not s_val:
                            new_data[field] = []
                            continue
                        
                        # Handle JSON
                        if s_val.startswith('[') and s_val.endswith(']'):
                            try:
                                new_data[field] = json.loads(s_val)
                                continue
                            except: pass
                        
                        # Handle CSV (if not eating_style)
                        if field != 'eating_style':
                            new_data[field] = [v.strip() for v in s_val.split(',') if v.strip()]
                            continue
                        
                    # Otherwise, just clean up the elements if they are strings
                    processed_list = []
                    for item in value:
                        if isinstance(item, str):
                            processed_list.extend([v.strip() for v in item.split(',') if v.strip()])
                        else:
                            processed_list.append(item)
                    new_data[field] = processed_list

        return super().to_internal_value(new_data)

    class Meta:
        model = ProfileModel
        fields = [
            'id',
            'user',
            'profile_name',
            'profile_image',
            'avatar',
            'country',
            'date_of_birth',
            'eating_style',
            'allergies',
            'medical_conditions',
            'magic_list',
            'is_active',
        ]
        # Make certain fields read-only
        read_only_fields = ['id', 'user']

    def validate(self, attrs):
        """
        Cross-field validation to ensure profile_image and avatar are mutually exclusive.
        
        Why: Business logic dictates that only one image source should be active.
        Setting one should automatically null the other to prevent confusion.
        """
        profile_image = attrs.get('profile_image')
        avatar = attrs.get('avatar')

        # If profile_image is provided, clear avatar
        if profile_image:
            # Use empty string instead of None to avoid NotNullViolation in some DB configurations
            attrs['avatar'] = ""
        # If avatar is provided and profile_image is not in the request, clear profile_image
        elif avatar and 'profile_image' in attrs:
            attrs['profile_image'] = None

        return attrs

    # ------------------- Custom Representation -------------------
    def to_representation(self, instance):
        """
        Customize the output representation to properly format eating_style.
        
        Why: The eating_style is stored in a through model (ProfileEatingStyle),
        so we need to manually construct the nested representation from the related objects.
        """
        data = super().to_representation(instance)
        
        # Optimize query with select_related to avoid N+1 queries
        es_links = instance.eating_style_links.select_related('eating_style')
        data['eating_style'] = [
            {
                "eating_style_name": link.eating_style.eating_style_name,
                "level": link.level
            }
            for link in es_links
        ]
        return data

    # ------------------- Custom Save Logic -------------------
    def _save_eating_styles(self, profile, eating_style_data):
        """
        Handle the many-to-many relationship with extra fields (level).
        
        Why: Django's built-in many-to-many handlers don't support through models
        with extra fields. We need to manually manage the ProfileEatingStyle entries.
        
        The delete-then-create pattern ensures we don't have orphaned records
        and maintains data integrity.
        """
        # Delete existing associations to prevent duplicates
        ProfileEatingStyle.objects.filter(profile=profile).delete()
        
        for item in eating_style_data:
            # Accept both 'eating_style_name' (for create) and 'name' (for compatibility)
            name = item.get("eating_style_name") or item.get("name")
            level = item.get("level", "Balanced")

            if not name:
                raise serializers.ValidationError(
                    {"eating_style": "Eating style name is required for each entry."}
                )

            try:
                style = EatingStyleModel.objects.get(eating_style_name=name)
            except EatingStyleModel.DoesNotExist:
                raise serializers.ValidationError(
                    {"eating_style": f"Eating style '{name}' not found."}
                )

            ProfileEatingStyle.objects.create(
                profile=profile,
                eating_style=style,
                level=level
            )

    def create(self, validated_data):
        """
        Override create to handle nested eating_style data.
        
        Why: DRF doesn't automatically handle nested writable serializers,
        so we extract the eating_style data before creating the profile,
        then manually save the relationships.
        """
        eating_styles = validated_data.pop('eating_style', [])
        
        # Set user from request context (should be done in view)
        if 'user' not in validated_data and self.context.get('request'):
            validated_data['user'] = self.context['request'].user
            
        profile = super().create(validated_data)
        
        if eating_styles:
            self._save_eating_styles(profile, eating_styles)
            
        return profile

    def update(self, instance, validated_data):
        """
        Override update to handle nested eating_style data.
        
        Why: Similar to create, we need to manually handle the through model updates.
        Using None check allows partial updates where eating_style isn't modified.
        """
        eating_styles = validated_data.pop('eating_style', None)
        profile = super().update(instance, validated_data)
        
        # Only update eating styles if explicitly provided in request
        if eating_styles is not None:
            self._save_eating_styles(profile, eating_styles)
            
        return profile


class ActivateProfileSerializer(serializers.Serializer):
    """For Swagger documentation only — no body actually needed."""
    # Keep read_only but provide example/default so UI shows something
    message = serializers.CharField(read_only=True, default='Profile activated successfully.')

# ---------------------------- OTP Serializers ----------------------------

class RequestOTPSerializer(serializers.Serializer):
    # default helps frontend quickly test the endpoint from Swagger
    email = serializers.EmailField(default='test+otp@example.com', help_text='Email to receive OTP')

    def validate_email(self, email):
        # You can enforce domain or app-specific validation here
        return email

    def create(self, validated_data):
        email = validated_data['email']
        otp = generate_otp()

        EmailOTPModel.objects.create(email=email, otp=otp)
        send_otp_via_email(email, otp)
        return {"detail": "OTP sent successfully."}


class VerifyOTPSerializer(serializers.Serializer):
    # Provide defaults so Swagger Try-it-out is prefilled
    email = serializers.EmailField(default='test+otp@example.com')
    otp = serializers.CharField(max_length=6, default='123456')
    language = serializers.ChoiceField(
        choices=[('English','English'), ('Spanish','Spanish'), ('French','French'), ('Bangla','Bangla')],
        required=False,
        default='English'
    )

    def validate(self, data):
        email = data.get('email')
        otp = data.get('otp')
        language = data.get('language', None)

        try:
            otp_obj = EmailOTPModel.objects.filter(email=email, otp=otp, is_used=False).latest('created_at')
        except EmailOTPModel.DoesNotExist:
            raise serializers.ValidationError("Invalid OTP.")

        if not otp_obj.is_valid():
            raise serializers.ValidationError("OTP expired or already used.")

        # mark OTP as used
        otp_obj.is_used = True
        otp_obj.save()

        # Get or create user (use manager to properly set unusable password for new users)
        try:
            user = CustomUserModel.objects.get(email=email)
        except CustomUserModel.DoesNotExist:
            user = CustomUserModel.objects.create_user(email=email)

        # Set language if provided
        if language:
            user.language = language
            user.save()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user.id,
                "email": user.email,
                "is_active": user.is_active,
                "paid_user": user.paid_user,
                "current_plan": user.current_plan,
                "language": user.language,
                "is_admin": user.is_superuser,
            }
        }
    

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()



class SocialUserRepresentationSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    profile_image = serializers.SerializerMethodField()

    class Meta:
        model = CustomUserModel
        fields = ['id', 'email', 'full_name', 'profile_image']

    def get_full_name(self, obj):
        try:
            active_profile = obj.profiles.filter(is_active=True).first()
            if active_profile:
                return active_profile.profile_name
        except:
            pass
        return obj.email.split('@')[0]

    def get_profile_image(self, obj):
        try:
            active_profile = obj.profiles.filter(is_active=True).first()
            if active_profile and active_profile.profile_image:
                return active_profile.profile_image.url
            elif active_profile and active_profile.avatar:
                return active_profile.avatar
        except:
            pass
        return "https://prommt.cc/profile_images/default_avatar.png"


class GoogleLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()


class AppleLoginSerializer(serializers.Serializer):
    id_token = serializers.CharField()
    email = serializers.EmailField(required=False, allow_null=True, allow_blank=True)

    def get_response(self):
        """
        Overrides default response to include refresh token
        """
        user = self.user
        refresh = RefreshToken.for_user(user)
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'email': user.email
            }
        }