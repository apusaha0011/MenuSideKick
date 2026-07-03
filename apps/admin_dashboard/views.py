from apps.users.models import CustomUserModel
from .models import *
from .serializers import *
from rest_framework import viewsets, status
from rest_framework.response import Response
from django.conf import settings
from core.utils.custompermissions import IsAdminOrReadOnly
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from django.db.models.functions import TruncMonth
from django.db.models import Count
from datetime import datetime

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

import boto3
from uuid import uuid4
import os

from .sigleton_structure import BaseSingletonAPIView


def _upload_file_to_s3(file_obj, key):
    """
    Uploads file_obj (file-like) to S3 under the given key.
    Returns the public URL for the uploaded object.
    """
    bucket = getattr(settings, "AWS_STORAGE_BUCKET_NAME", None)
    if not bucket:
        raise RuntimeError("AWS_STORAGE_BUCKET_NAME not configured in settings")

    aws_access_key = getattr(settings, "AWS_ACCESS_KEY_ID", None)
    aws_secret = getattr(settings, "AWS_SECRET_ACCESS_KEY", None)
    region = getattr(settings, "AWS_S3_REGION_NAME", None)
    custom_domain = getattr(settings, "AWS_S3_CUSTOM_DOMAIN", None)

    s3_client = boto3.client(
        "s3",
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret,
        region_name=region
    )

    # upload
    s3_client.upload_fileobj(file_obj, bucket, key)

    # build URL
    if custom_domain:
        return f"https://{custom_domain}/{key}"
    if region:
        return f"https://{bucket}.s3.{region}.amazonaws.com/{key}"
    return f"https://{bucket}.s3.amazonaws.com/{key}"


class S3UploadMixin:
    """
    Mixin to handle request.FILES -> upload to S3 -> inject S3 URL into serializer input.
    Child viewsets should set `file_field_names` to a list of fields to process.
    """
    file_field_names = []  # override in child
    # ensure multipart/form-data requests are parsed by default for file uploads
    parser_classes = (MultiPartParser, FormParser)

    def _prepare_data_with_files(self, request):
        # make mutable copy of incoming data
        data = request.data.copy()
        for field_name in getattr(self, "file_field_names", []):
            if field_name in request.FILES:
                file_obj = request.FILES[field_name]
                filename = os.path.basename(file_obj.name).replace(" ", "_")
                key = f"{self.__class__.__name__.lower()}/{uuid4().hex}_{filename}"
                url = _upload_file_to_s3(file_obj, key)
                data[field_name] = url
        return data

    def create(self, request, *args, **kwargs):
        try:
            data = self._prepare_data_with_files(request)
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop("partial", False)
            instance = self.get_object()
            data = self._prepare_data_with_files(request)
            serializer = self.get_serializer(instance, data=data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data)
        except Exception as e:
             return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


#------------------------Settings Views------------------------

class PrivacyPolicyAPIView(BaseSingletonAPIView):
    model = PrivacyPolicyModel
    serializer_class = PrivacyPolicySerializer
    folder_name = "privacy_policy"

class TermsAndConditionsAPIView(BaseSingletonAPIView):
    model = TermsAndConditionsModel
    serializer_class = TermsAndConditionsSerializer
    folder_name = "terms_conditions"

class AboutUsAPIView(BaseSingletonAPIView):
    model = AboutUsModel
    serializer_class = AboutUsSerializer
    folder_name = "about_us"


#------------------------Category Views------------------------


class EatingStyleViewSet(S3UploadMixin, viewsets.ModelViewSet):
    queryset = EatingStyleModel.objects.all()
    serializer_class = EatingStyleSerializer
    permission_classes = [IsAdminOrReadOnly]
    file_field_names = ["eating_style_icon"]

    parser_classes = (MultiPartParser, FormParser)

    @swagger_auto_schema(
        manual_parameters=[openapi.Parameter('eating_style_icon',openapi.IN_FORM,description="Upload an image (JPG, PNG, etc.)",type=openapi.TYPE_FILE,required=False),],consumes=['multipart/form-data'])
    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AllergyViewSet(S3UploadMixin, viewsets.ModelViewSet):
    queryset = AllergyModel.objects.all()
    serializer_class = AllergySerializer
    permission_classes = [IsAdminOrReadOnly]
    file_field_names = ["allergy_icon"]
    parser_classes = (MultiPartParser, FormParser)

    @swagger_auto_schema(
        manual_parameters=[openapi.Parameter('allergy_icon',openapi.IN_FORM,description="Upload an image (JPG, PNG, etc.)",type=openapi.TYPE_FILE,required=False),],consumes=['multipart/form-data'])
    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class MedicalConditionViewSet(S3UploadMixin, viewsets.ModelViewSet):
    queryset = MedicalConditionModel.objects.all()
    serializer_class = MedicalConditionSerializer
    permission_classes = [IsAdminOrReadOnly]
    file_field_names = ["medical_condition_icon"]

    parser_classes = (MultiPartParser, FormParser)

    @swagger_auto_schema(
        manual_parameters=[openapi.Parameter('medical_condition_icon',openapi.IN_FORM,description="Upload an image (JPG, PNG, etc.)",type=openapi.TYPE_FILE,required=False),],consumes=['multipart/form-data'])
    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class AvatarViewSet(S3UploadMixin, viewsets.ModelViewSet):
    queryset = AvatarModel.objects.all()
    serializer_class = AvatarSerializer
    permission_classes = [IsAdminOrReadOnly]
    file_field_names = ["avatar_icon"]
    parser_classes = (MultiPartParser, FormParser)

    @swagger_auto_schema(
        manual_parameters=[openapi.Parameter('avatar_icon',openapi.IN_FORM,description="Upload an image (JPG, PNG, etc.)",type=openapi.TYPE_FILE,required=False),],consumes=['multipart/form-data'])
    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
#-----------------------Feedback Views------------------------
class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = FeedbackModel.objects.all()
    serializer_class = FeedbackSerializer
    permission_classes = [AllowAny]



#-----------------------User Statistics View------------------------
class UserStatisticsView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        year_param = request.query_params.get('year')
        
        if year_param:
            try:
                year = int(year_param)
                # Validate year range (reasonable bounds)
                if year < 2000 or year > datetime.now().year + 1:
                    return Response(
                        {"error": f"Year must be between 2000 and {datetime.now().year + 1}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except ValueError:
                return Response(
                    {"error": "Invalid year parameter. Must be an integer."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            year = datetime.now().year

        try:
            users_in_year = CustomUserModel.objects.filter(
                date_joined__year=year
            )

            total_users = users_in_year.count()

            monthly_stats = (
                users_in_year
                .annotate(month=TruncMonth('date_joined'))
                .values('month')
                .annotate(user_count=Count('id'))
                .order_by('month')
            )

            monthly_data = []
            month_names = [
                'January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November', 'December'
            ]
            
            for stat in monthly_stats:
                month_num = stat['month'].month
                monthly_data.append({
                    'month': month_num,
                    'month_name': month_names[month_num - 1],
                    'user_count': stat['user_count']
                })

            response_data = {
                'year': year,
                'total_users': total_users,
                'monthly_data': monthly_data
            }

            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)