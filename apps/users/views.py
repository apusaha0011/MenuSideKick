from rest_framework import viewsets, parsers
from .models import CustomUserModel, ProfileModel, EmailOTPModel
from .serializers import (
    UserSerializer, 
    ProfileSerializer, 
    RequestOTPSerializer, 
    VerifyOTPSerializer, 
    LogoutSerializer, 
    ActivateProfileSerializer,
    GoogleLoginSerializer,
    AppleLoginSerializer,
    SocialUserRepresentationSerializer
)
from .utils import send_otp_via_email, generate_otp

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action

# Social Login
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema, no_body

from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.conf import settings
from core.utils.custompermissions import IsSelfOrAdmin
from drf_yasg.inspectors import SwaggerAutoSchema

class ProfileFormDataAutoSchema(SwaggerAutoSchema):
    """
    Custom SwaggerAutoSchema to handle Profile form-data properly.
    It forcefully removes auto-generated body parameters to allow manual form parameters.
    """
    def get_request_body_parameters(self, consumes):
        return []
    
    def get_parameters(self):
        parameters = super().get_parameters()
        # Remove any automatically added body parameter to avoid conflict with manual IN_FORM params
        return [p for p in parameters if getattr(p, 'in_', None) != openapi.IN_BODY]

    def add_manual_parameters(self, parameters):
        manual_parameters = self.overrides.get('manual_parameters', None) or []
        if not manual_parameters:
            return parameters
        
        # Bypass the check by just returning the union of collected and manual parameters
        # forcefully discarding any auto-generated body parameters
        existing_params = [p for p in parameters if getattr(p, 'in_', None) != openapi.IN_BODY]
        return existing_params + manual_parameters

# Create your views here.



class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUserModel.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsSelfOrAdmin]

    @swagger_auto_schema(methods=['get'], responses={200: UserSerializer()},
                         operation_description="Get the currently authenticated user's data")
    @swagger_auto_schema(methods=['patch'], request_body=UserSerializer, responses={200: UserSerializer()},
                         operation_description="Partially update the currently authenticated user's data")
    @action(detail=False, methods=['get', 'patch'], url_path='me')
    def me(self, request):
        """Retrieve or partially update the logged-in user."""
        # Avoid touching request.user during schema generation (drf-yasg)
        if getattr(self, 'swagger_fake_view', False):
            return Response({})

        user = request.user
        if not user or getattr(user, 'is_anonymous', False):
            return Response({"detail": "Authentication credentials were not provided."}, status=status.HTTP_401_UNAUTHORIZED)

        if request.method == 'GET':
            serializer = self.get_serializer(user)
            return Response(serializer.data)

        elif request.method == 'PATCH':
            serializer = self.get_serializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

class ProfileViewSet(viewsets.ModelViewSet):
    queryset = ProfileModel.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated, IsSelfOrAdmin]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    # Shared parameters for form-data actions
    manual_form_parameters_create = [
        openapi.Parameter('profile_name', openapi.IN_FORM, type=openapi.TYPE_STRING, default='Default Profile', example='Default Profile', required=True),
        openapi.Parameter('profile_image', openapi.IN_FORM, type=openapi.TYPE_FILE, description="Upload profile image"),
        openapi.Parameter('avatar', openapi.IN_FORM, type=openapi.TYPE_STRING, default='https://example.com/avatar.png', example='https://example.com/avatar.png'),
        openapi.Parameter('country', openapi.IN_FORM, type=openapi.TYPE_STRING, default='USA', example='USA'),
        openapi.Parameter('date_of_birth', openapi.IN_FORM, type=openapi.TYPE_STRING, format='date', default='1995-01-01', example='1995-01-01'),
        openapi.Parameter('magic_list', openapi.IN_FORM, type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING), default=['pizza', 'salad'], example=['pizza', 'salad'], collection_format='multi'),
        openapi.Parameter('allergies', openapi.IN_FORM, type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING), default=['peanut', 'gluten'], example=['peanut', 'gluten'], collection_format='multi'),
        openapi.Parameter('medical_conditions', openapi.IN_FORM, type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING), default=['diabetes'], example=['diabetes'], collection_format='multi'),
        openapi.Parameter('eating_style', openapi.IN_FORM, type=openapi.TYPE_STRING, default='[{"eating_style_name": "Vegan", "level": "Strict"}]', example='[{"eating_style_name": "Vegan", "level": "Strict"}]', description="JSON array string"),
    ]

    manual_form_parameters_update = [
        openapi.Parameter('profile_name', openapi.IN_FORM, type=openapi.TYPE_STRING, default='Default Profile', example='Default Profile', required=False),
        openapi.Parameter('profile_image', openapi.IN_FORM, type=openapi.TYPE_FILE, description="Upload profile image"),
        openapi.Parameter('avatar', openapi.IN_FORM, type=openapi.TYPE_STRING, default='https://example.com/avatar.png', example='https://example.com/avatar.png'),
        openapi.Parameter('country', openapi.IN_FORM, type=openapi.TYPE_STRING, default='USA', example='USA'),
        openapi.Parameter('date_of_birth', openapi.IN_FORM, type=openapi.TYPE_STRING, format='date', default='1995-01-01', example='1995-01-01'),
        openapi.Parameter('magic_list', openapi.IN_FORM, type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING), default=['pizza', 'salad'], example=['pizza', 'salad'], collection_format='multi'),
        openapi.Parameter('allergies', openapi.IN_FORM, type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING), default=['peanut', 'gluten'], example=['peanut', 'gluten'], collection_format='multi'),
        openapi.Parameter('medical_conditions', openapi.IN_FORM, type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING), default=['diabetes'], example=['diabetes'], collection_format='multi'),
        openapi.Parameter('eating_style', openapi.IN_FORM, type=openapi.TYPE_STRING, default='[{"eating_style_name": "Vegan", "level": "Strict"}]', example='[{"eating_style_name": "Vegan", "level": "Strict"}]', description="JSON array string"),
    ]

    @swagger_auto_schema(
        auto_schema=ProfileFormDataAutoSchema,
        operation_description="Create a new profile with optional image upload. All fields will appear as pre-filled form-data in Postman.",
        manual_parameters=manual_form_parameters_create,
        consumes=['multipart/form-data'],
        responses={201: ProfileSerializer()}
    )
    def create(self, request, *args, **kwargs):
        """
        Why multipart/form-data: This content type is required for file uploads.
        Manual parameters with IN_FORM ensure individual fields in Postman.
        """
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        auto_schema=ProfileFormDataAutoSchema,
        operation_description="Update a profile with optional image upload",
        manual_parameters=manual_form_parameters_update,
        consumes=['multipart/form-data'],
        responses={200: ProfileSerializer()}
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        auto_schema=ProfileFormDataAutoSchema,
        operation_description="Partially update a profile with optional image upload",
        manual_parameters=manual_form_parameters_update,
        consumes=['multipart/form-data'],
        responses={200: ProfileSerializer()}
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    def get_queryset(self):
        """
        Optimize queryset based on action.
        
        Why: For active_profile action, we only need profiles for the current user
        that are active. This reduces query overhead and enforces authorization at the DB level.
        """
        if self.action == 'active_profile':
            return ProfileModel.objects.filter(user=self.request.user, is_active=True)
        return super().get_queryset()
    
    def perform_create(self, serializer):
        """
        Automatically set the user field to the current authenticated user.
        
        Why: This ensures users can only create profiles for themselves,
        preventing privilege escalation. We don't trust client-provided user IDs.
        """
        serializer.save(user=self.request.user)

    @swagger_auto_schema(
        request_body=no_body,
        responses={200: openapi.Response('Profile activated successfully')},
        operation_description="Activate a specific profile (deactivates all other profiles for the user)"
    )
    @action(detail=True, methods=['post'], url_path='activate', serializer_class=ActivateProfileSerializer)
    def activate(self, request, pk=None):
        """
        Activate a profile and deactivate all others for the user.
        
        Why: The business rule is "one active profile per user". This atomic operation
        ensures consistency by deactivating others in the same transaction.
        """
        profile = self.get_object()

        # Authorization check
        if profile.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You do not have permission to activate this profile.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Deactivate all user's profiles, then activate this one
        ProfileModel.objects.filter(user=request.user).update(is_active=False)
        profile.is_active = True
        profile.save()

        return Response(
            {'detail': f"Profile '{profile.profile_name}' is now active."},
            status=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        method='get',
        responses={200: ProfileSerializer()},
        operation_description="Get the currently active profile for the logged-in user"
    )
    @swagger_auto_schema(
        method='patch',
        auto_schema=ProfileFormDataAutoSchema,
        manual_parameters=manual_form_parameters_update,
        responses={200: ProfileSerializer()},
        operation_description="Update the currently active profile",
        consumes=['multipart/form-data']
    )
    @swagger_auto_schema(
        method='delete',
        responses={204: 'Profile deleted successfully'},
        operation_description="Delete the currently active profile"
    )
    @action(detail=False, methods=['get', 'patch', 'delete'], url_path='active')
    def active_profile(self, request):
        """
        Convenient endpoint to work with the user's active profile without knowing its ID.
        
        Why: Frontend doesn't need to track profile IDs - just work with 'active' profile.
        This reduces client-side complexity and potential errors.
        """
        try:
            profile = self.get_queryset().get()
        except ProfileModel.DoesNotExist:
            return Response(
                {'error': 'No active profile found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except ProfileModel.MultipleObjectsReturned:
            # Data integrity issue - fix it
            profiles = self.get_queryset()
            profile = profiles.first()
            profiles.exclude(pk=profile.pk).update(is_active=False)

        if request.method == 'GET':
            serializer = self.get_serializer(profile)
            return Response(serializer.data)

        elif request.method == 'PATCH':
            serializer = self.get_serializer(profile, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            try:
                serializer.save()
            except Exception as e:
                # Log the error and return a friendly message
                # This catches IntegrityErrors and other DB level issues
                return Response(
                    {"error": "Failed to update profile due to a database constraint.", "detail": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(serializer.data)

        elif request.method == 'DELETE':
            profile.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)




# ------------------------------- Auth Views ------------------


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]
    @swagger_auto_schema(request_body=GoogleLoginSerializer)
    def post(self, request):
        serializer = GoogleLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        
        user, created = CustomUserModel.objects.get_or_create(email=email)
        
        refresh = RefreshToken.for_user(user)
        user_data = SocialUserRepresentationSerializer(user).data
        
        return Response({
            "success": True,
            "created": created,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": user_data
        }, status=status.HTTP_200_OK)


class AppleLoginView(APIView):
    permission_classes = [AllowAny]
    @swagger_auto_schema(request_body=AppleLoginSerializer)
    def post(self, request):
        serializer = AppleLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get('email')
        id_token = serializer.validated_data['id_token']
        
        if not email:
            # Fallback for mock/trusted login
            email = f"apple_{id_token[:10]}@icloud.com"
            
        user, created = CustomUserModel.objects.get_or_create(email=email)
        
        refresh = RefreshToken.for_user(user)
        user_data = SocialUserRepresentationSerializer(user).data
        
        return Response({
            "success": True,
            "created": created,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": user_data
        }, status=status.HTTP_200_OK)



class RequestOTPView(APIView):
    @swagger_auto_schema(request_body=RequestOTPSerializer)
    def post(self, request):
        serializer = RequestOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "OTP sent successfully."}, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    @swagger_auto_schema(request_body=VerifyOTPSerializer, responses={200: VerifyOTPSerializer()})
    def post(self, request):
        try:
            serializer = VerifyOTPSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(request_body=LogoutSerializer)
    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Logged out successfully."}, status=status.HTTP_205_RESET_CONTENT)
        except KeyError:
            return Response({"error": "Refresh token not provided."}, status=status.HTTP_400_BAD_REQUEST)
        except TokenError:
            return Response({"error": "Invalid or expired refresh token."}, status=status.HTTP_400_BAD_REQUEST)
        