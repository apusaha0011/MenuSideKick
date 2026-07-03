from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from django.conf import settings
import boto3
from uuid import uuid4
import os

from rest_framework.permissions import AllowAny

from .models import (
    PrivacyPolicyModel,
    TermsAndConditionsModel,
    AboutUsModel
)
from .serializers import (
    PrivacyPolicySerializer,
    TermsAndConditionsSerializer,
    AboutUsSerializer
)


# ========= S3 UPLOAD helper ========= #

def upload_to_s3(file_obj, folder):
    bucket = settings.AWS_STORAGE_BUCKET_NAME
    region = settings.AWS_S3_REGION_NAME
    access = settings.AWS_ACCESS_KEY_ID
    secret = settings.AWS_SECRET_ACCESS_KEY
    custom_domain = settings.AWS_S3_CUSTOM_DOMAIN

    s3 = boto3.client(
        "s3",
        aws_access_key_id=access,
        aws_secret_access_key=secret,
        region_name=region
    )

    filename = os.path.basename(file_obj.name).replace(" ", "_")
    key = f"{folder}/{uuid4().hex}_{filename}"

    s3.upload_fileobj(file_obj, bucket, key)

    if custom_domain:
        return f"https://{custom_domain}/{key}"
    return f"https://{bucket}.s3.{region}.amazonaws.com/{key}"


# ========= BASE SINGLETON VIEW ========= #

class BaseSingletonAPIView(APIView):
    """Reusable Singleton API (GET, POST, PATCH)."""
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [AllowAny]

    model = None
    serializer_class = None
    folder_name = None  # for s3 folder

    def get_object(self):
        return self.model.objects.first()

    # ---------------- GET ---------------- #
    @swagger_auto_schema(responses={200: "OK"})
    def get(self, request):
        obj = self.get_object()
        if not obj:
            return Response({"error": "No data found"}, status=404)
        return Response(self.serializer_class(obj).data)

    # ---------------- POST (create only once) ------------ #
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "content",
                openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="Text content"
            ),
            openapi.Parameter(
                "image",
                openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=False,
                description="Upload image"
            ),
        ],
        consumes=["multipart/form-data"],
        responses={201: PrivacyPolicySerializer}
    )
    def post(self, request):
        if self.get_object():
            return Response(
                {"error": "Entry already exists. Use PATCH to update."},
                status=400
            )

        data = request.data.copy()

        # Handle file upload
        if "image" in request.FILES:
            data["image"] = upload_to_s3(request.FILES["image"], self.folder_name)

        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=201)

    # ---------------- PATCH (update existing) ------------ #
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "content",
                openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description="Text content"
            ),
            openapi.Parameter(
                "image",
                openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=False,
                description="Upload image"
            ),
        ],
        consumes=["multipart/form-data"],
        responses={201: PrivacyPolicySerializer}
    )
    def patch(self, request):
        obj = self.get_object()
        if not obj:
            return Response({"error": "No entry exists to update"}, status=404)

        data = request.data.copy()

        # Handle file upload
        if "image" in request.FILES:
            data["image"] = upload_to_s3(request.FILES["image"], self.folder_name)

        serializer = self.serializer_class(obj, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)
