from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import get_object_or_404

from .bots.combo_creator_ai import combo_created_json
from .bots.platter_designer_ai import avoid_list_json

from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import IsAuthenticated, AllowAny 
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser

from .models import (
                    MyPlateModel,
                    ConversationModel, 
                    MessageModel,
                    ScannedDocumentModel
                    )
from .serializers import (
                    MyPlateSerializer,
                    MagicListRequestSerializer, 
                    MessageSerializer, 
                    ChatRequestSerializer, 
                    ConversationSerializer,
                    ScannedDocumentSerializer
                    )
from apps.users.models import CustomUserModel, ProfileModel

from core.settings import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_STORAGE_BUCKET_NAME,
    AWS_S3_CUSTOM_DOMAIN,
    AWS_S3_REGION_NAME,
)
import boto3
import uuid
import json





def upload_file_to_s3(file_obj, folder_prefix='uploads'):
    """Upload file_obj to S3 and return (file_url, key).

    Raises serializers.ValidationError on failure.
    """
    filename = getattr(file_obj, 'name', None) or str(uuid.uuid4())
    file_extension = filename.split('.')[-1] if '.' in filename else ''
    key = f"{folder_prefix}/{uuid.uuid4()}.{file_extension}" if file_extension else f"{folder_prefix}/{uuid.uuid4()}"

    s3 = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_S3_REGION_NAME
    )

    try:
        try:
            file_obj.seek(0)
        except Exception:
            pass
        s3.upload_fileobj(file_obj, AWS_STORAGE_BUCKET_NAME, key)
    except Exception as e:
        raise serializers.ValidationError({"detail": f"Failed to upload file to S3: {str(e)}"})

    if AWS_S3_CUSTOM_DOMAIN:
        file_url = f"https://{AWS_S3_CUSTOM_DOMAIN.rstrip('/')}/{key}"
    else:
        file_url = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com/{key}"

    return file_url, key

import logging
import boto3
import uuid
import json

logger = logging.getLogger(__name__)

from .bots.magiclist_ai import generate_magic_list_json
from .bots.chatbot_ai import generate_ai_reply
from .bots.ocr_ai import generate_ocr_analysis


from drf_yasg import openapi

files_param = openapi.Parameter(
    name='files',
    in_=openapi.IN_FORM,
    type=openapi.TYPE_FILE,
    required=True,
    description="Upload images for OCR",
    collection_format='multi'
)



# Create your views here.

# ========================= MyPlate Views (list/create + detail) =========================


class MyPlateListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def _get_active_profile(self):
        user = self.request.user
        return ProfileModel.objects.filter(user=user, is_active=True).first()

    @swagger_auto_schema(
        responses={200: MyPlateSerializer(many=True)},
        operation_description="List all MyPlate items for the logged-in user's active profile"
    )
    def get(self, request):
        profile = self._get_active_profile()
        if not profile:
            return Response({"error": "No active profile found."}, status=status.HTTP_400_BAD_REQUEST)

        myplates = MyPlateModel.objects.filter(user=request.user, profile=profile).order_by('-created_at')
        serializer = MyPlateSerializer(myplates, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('meal_name', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('image', openapi.IN_FORM, type=openapi.TYPE_FILE, required=True, description='Image file for the meal (JPG/PNG) — this will be uploaded to S3 and the resulting image_url stored automatically'),
            openapi.Parameter('plate_combo', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
        ],
        responses={201: MyPlateSerializer()},
        operation_description="Create a new MyPlate item by uploading an image; the image_url will be set automatically from the uploaded S3 object"
    )
    def post(self, request):
        profile = self._get_active_profile()
        if not profile:
            return Response({"error": "No active profile found."}, status=status.HTTP_400_BAD_REQUEST)

        image_file = request.FILES.get('image')
        image_url = request.POST.get('image_url')

        if image_file:
            try:
                file_url, key = upload_file_to_s3(image_file, folder_prefix='myplate_images')
                image_url = file_url
            except serializers.ValidationError as e:
                return Response({"error": str(e.detail)}, status=status.HTTP_400_BAD_REQUEST)

        if not image_url:
            return Response({"error": "Either an image file or 'image_url' must be provided."}, status=status.HTTP_400_BAD_REQUEST)

        data = request.POST.copy()
        data['image_url'] = image_url

        serializer = MyPlateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, profile=profile)
        return Response(serializer.data, status=status.HTTP_201_CREATED)



class MyPlateDetailView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def _get_myplate(self, user, pk):
        profile = ProfileModel.objects.filter(user=user, is_active=True).first()
        if not profile:
            return None, None
        try:
            myplate = MyPlateModel.objects.get(id=pk, user=user, profile=profile)
            return myplate, profile
        except MyPlateModel.DoesNotExist:
            return None, None

    @swagger_auto_schema(
        responses={200: MyPlateSerializer()},
        operation_description="Retrieve a specific MyPlate item"
    )
    def get(self, request, pk):
        myplate, profile = self._get_myplate(request.user, pk)
        if not myplate:
            return Response({"error": "MyPlate not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = MyPlateSerializer(myplate)
        return Response(serializer.data)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('meal_name', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('image', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description='Replace image by uploading a new file; image_url will be updated automatically'),
            openapi.Parameter('plate_combo', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
        ],
        responses={200: MyPlateSerializer()},
        operation_description="Partially update a MyPlate item (supports image upload); image_url is populated from the uploaded image"
    )
    def patch(self, request, pk):
        myplate, profile = self._get_myplate(request.user, pk)
        if not myplate:
            return Response({"error": "MyPlate not found."}, status=status.HTTP_404_NOT_FOUND)

        data = request.POST.copy()
        image_file = request.FILES.get('image')
        if image_file:
            try:
                file_url, key = upload_file_to_s3(image_file, folder_prefix='myplate_images')
                data['image_url'] = file_url
            except serializers.ValidationError as e:
                return Response({"error": str(e.detail)}, status=status.HTTP_400_BAD_REQUEST)

            serializer = MyPlateSerializer(myplate, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

    @swagger_auto_schema(
        responses={204: 'No Content'},
        operation_description="Delete a MyPlate item"
    )
    def delete(self, request, pk):
        myplate, profile = self._get_myplate(request.user, pk)
        if not myplate:
            return Response({"error": "MyPlate not found."}, status=status.HTTP_404_NOT_FOUND)

        myplate.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MagicListView(APIView):
    @swagger_auto_schema(
        request_body=MagicListRequestSerializer,
        responses={200: 'AI processed and returned food recommendations.'}
    )
    def post(self, request):
        serializer = MagicListRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data


        # Simulate AI logic (to be replaced later)
        result = generate_magic_list_json(data)

        # Result already contains 'magic_list' key, so return it directly
        return Response(result, status=status.HTTP_200_OK)
    

class NewConversationView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={201: ConversationSerializer},
        security=[{"Bearer": []}]
    )
    def post(self, request):
        user = request.user
        profile = ProfileModel.objects.filter(user=user, is_active=True).first()
        if not profile:
            return Response({"error": "No active profile found."}, status=400)

        # create new blank conversation
        conversation = ConversationModel.objects.create(
            user=user,
            profile=profile,
            title="New Chat"
        )
        serializer = ConversationSerializer(conversation, context={'request': request})
        return Response(serializer.data, status=201)


class ChatView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=ChatRequestSerializer,
        responses={200: ConversationSerializer},
        security=[{"Bearer": []}]
    )
    def post(self, request):
        user = request.user
        if not user or getattr(user, "is_anonymous", False):
            return Response({"detail": "Authentication credentials were not provided."},
                            status=status.HTTP_401_UNAUTHORIZED)

        # ✅ auto-detect active profile
        profile = ProfileModel.objects.filter(user=user, is_active=True).first()
        if not profile:
            return Response({"error": "No active profile found. Please create or activate one."},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_message = serializer.validated_data['message']

        with transaction.atomic():
            # ✅ auto-select or create conversation
            conversation = ConversationModel.objects.filter(
                user=user, profile=profile
            ).order_by('-updated_at').first()

            if not conversation or (conversation.messages.count() > 50):  # optional: limit chat length
                conversation = ConversationModel.objects.create(
                    user=user,
                    profile=profile,
                    title=user_message[:80]
                )

            # save user message
            MessageModel.objects.create(
                conversation=conversation,
                content=user_message,
                sender='user'
            )

            # prepare history + profile info
            history = [{"role": m.sender, "content": m.content} for m in conversation.messages.all()]
            profile_payload = {
                "eating_style": list(profile.eating_style.values_list('eating_style_name', flat=True)),
                "allergies": list(profile.allergies.values_list('allergy_name', flat=True)),
                "medical_conditions": list(profile.medical_conditions.values_list('medical_condition_name', flat=True)),
                "magic_list": profile.magic_list or [],
                "profile_name": profile.profile_name,
                "date_of_birth": profile.date_of_birth.isoformat() if profile.date_of_birth else None,
                "preferred_language": user.language,
                "country": profile.country,
            }

            # get AI reply
            ai_response = generate_ai_reply(history, user_message, profile_payload)
            reply_text = ai_response.get('reply') if isinstance(ai_response, dict) else str(ai_response)

            MessageModel.objects.create(
                conversation=conversation,
                content=reply_text,
                sender='ai'
            )

        response_data = ConversationSerializer(conversation, context={'request': request}).data
        return Response(response_data, status=status.HTTP_200_OK)

class ConversationListView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={200: ConversationSerializer(many=True)},
        security=[{"Bearer": []}]
    )
    def get(self, request):
        user = request.user
        profile = ProfileModel.objects.filter(user=user, is_active=True).first()
        if not profile:
            return Response({"error": "No active profile found."}, status=400)

        qs = ConversationModel.objects.filter(user=user, profile=profile).order_by('-updated_at')
        data = ConversationSerializer(qs, many=True, context={'request': request}).data
        return Response(data, status=200)


class ConversationMessagesView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={200: MessageSerializer(many=True)},
        security=[{"Bearer": []}]
    )
    def get(self, request, pk):
        user = request.user
        profile = ProfileModel.objects.filter(user=user, is_active=True).first()
        if not profile:
            return Response({"error": "No active profile found."}, status=400)

        conversation = get_object_or_404(ConversationModel, id=pk, user=user, profile=profile)
        msgs = conversation.messages.order_by('created_at')
        data = MessageSerializer(msgs, many=True, context={'request': request}).data
        return Response(data, status=200)


class ConversationDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={204: 'Deleted', 404: 'Not found'},
        security=[{"Bearer": []}]
    )
    def delete(self, request, pk):
        user = request.user
        profile = ProfileModel.objects.filter(user=user, is_active=True).first()
        if not profile:
            return Response({"error": "No active profile found."}, status=400)

        conversation = get_object_or_404(ConversationModel, id=pk, user=user, profile=profile)
        conversation.delete()
        return Response(status=204)

class SummaryAutoView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={200: 'Summaries created/updated'},
        security=[{"Bearer": []}]
    )
    def post(self, request):
        """
        Trigger automatic summarization for older conversations.
        This is a lightweight stub; replace with a background task (Celery/RQ) calling your summarizer.
        """
        user = request.user
        if not user or getattr(user, "is_anonymous", False):
            return Response({"detail": "Authentication credentials were not provided."}, status=status.HTTP_401_UNAUTHORIZED)

        # Example: summarize conversations not updated in the last 30 days
        threshold = timezone.now() - timedelta(days=30)
        conversations = ConversationModel.objects.filter(user=user, updated_at__lt=threshold)

        updated_count = 0

        def _summarize_conversation(conv):
            # Placeholder summarizer - replace with AI-based summarization and background processing
            msgs = conv.messages.order_by('created_at').values_list('content', flat=True)
            preview = " ".join(list(msgs)[-10:])  # last 10 messages
            return f"Auto-summary (preview): {preview[:500]}"

        for conv in conversations:
            conv.summary = _summarize_conversation(conv)
            conv.save(update_fields=['summary', 'updated_at'])
            updated_count += 1

        return Response({"summaries_updated": updated_count}, status=status.HTTP_200_OK)
    

class OCRView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    @swagger_auto_schema(
        operation_description="Upload one or multiple images/PDFs for OCR analysis.",
        manual_parameters=[
            openapi.Parameter(
                name="files",
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=True,
                description="One or multiple files to upload",
                multiple=True,
            )
        ],
        responses={200: "OCR result returned"},
    )
    def post(self, request):
        user = request.user
        if not user or user.is_anonymous:
            return Response({"detail": "Authentication required"}, status=401)

        profile = ProfileModel.objects.filter(user=user, is_active=True).first()
        if not profile:
            return Response({"error": "No active profile found. Please create and activate a profile first."}, status=400)

        files = request.FILES.getlist("files")
        if not files:
            return Response({"error": "No files were uploaded"}, status=400)

        all_extracted_text = []
        file_urls = []

        # Initialize Textract client
        textract = boto3.client(
            'textract',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_S3_REGION_NAME
        )

        for file_obj in files:
            # 1. Upload to S3 (Required for Textract PDF processing)
            try:
                file_url, file_key = upload_file_to_s3(file_obj, folder_prefix='ocr_uploads')
                file_urls.append(file_url)
            except Exception as e:
                logger.exception(f"Failed to upload {file_obj.name} to S3")
                return Response({"error": f"Failed to upload {file_obj.name} to S3: {str(e)}"}, status=500)

            # 2. Cloud OCR Processing (AWS Textract)
            try:
                # Textract natively supports PDF and images from S3
                # We use detect_document_text for simple images or analyze_document for complex ones/PDFs.
                # Here we use analyze_document to be more robust.
                
                response = textract.analyze_document(
                    Document={"S3Object": {"Bucket": AWS_STORAGE_BUCKET_NAME, "Name": file_key}},
                    FeatureTypes=["TABLES", "FORMS"]
                )
                
                text_segments = []
                for block in response.get("Blocks", []):
                    if block.get("BlockType") == "LINE" and block.get("Text"):
                        text_segments.append(block["Text"])

                file_text = "\n".join(text_segments)
                all_extracted_text.append(file_text)

            except Exception as e:
                logger.exception(f"OCR analysis failed for {file_obj.name}")
                return Response({
                    "error": f"OCR analysis failed for {file_obj.name}",
                    "detail": str(e)
                }, status=500)

        # Merge text from all files
        combined_text = "\n\n".join(all_extracted_text)

        # Prepare profile payload
        profile_payload = {
            "eating_style": list(profile.eating_style.values_list("eating_style_name", flat=True)),
            "allergies": list(profile.allergies.values_list("allergy_name", flat=True)),
            "medical_conditions": list(profile.medical_conditions.values_list("medical_condition_name", flat=True)),
            "magic_list": profile.magic_list or [],
            "profile_name": profile.profile_name,
            "date_of_birth": profile.date_of_birth.isoformat() if profile.date_of_birth else None,
            "country": profile.country,
        }

        # AI analysis
        try:
            ai_analysis = generate_ocr_analysis(profile_payload, combined_text)
        except Exception as e:
            ai_analysis = {"error": "AI analysis failed", "detail": str(e)}

        # Save single combined record (cleaner)
        scanned = ScannedDocumentModel.objects.create(
            user=user,
            profile=profile,
            file_urls=file_urls,
            extracted_text=combined_text,
            ai_reply=ai_analysis
        )

        return Response(ai_analysis, status=200)
    

class ScannedDocumentViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = ScannedDocumentModel.objects.all()
    serializer_class = ScannedDocumentSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return super().get_queryset().none()

        user = self.request.user
        return super().get_queryset().filter(user=user)

    @swagger_auto_schema(
        methods=['get'], responses={200: ScannedDocumentSerializer(many=True)},
        operation_description="List scanned documents for the logged-in user's active profile"
    )
    @action(detail=False, methods=['get'], url_path='active')
    def active(self, request):
        if getattr(self, 'swagger_fake_view', False):
            return Response([])

        user = request.user
        profile = ProfileModel.objects.filter(user=user, is_active=True).first()
        if not profile:
            return Response({"error": "No active profile found. Please create or activate a profile."}, status=status.HTTP_400_BAD_REQUEST)

        qs = self.get_queryset().filter(profile=profile).order_by('-uploaded_at')
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
    

class ComboView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema()
    def get(self, request, user_id, profile_name):
        try:
            user = CustomUserModel.objects.filter(id=user_id).first()
        except CustomUserModel.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        
        profile = ProfileModel.objects.filter(user=user, profile_name=profile_name).first()

        if not profile:
            return Response({"error": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)
        
        eating_style = list(profile.eating_style.values_list('eating_style_name', flat=True))
        allergies = list(profile.allergies.values_list('allergy_name', flat=True))
        medical_conditions = list(profile.medical_conditions.values_list('medical_condition_name', flat=True))
        magic_list = profile.magic_list
        
        combo_response = combo_created_json(
            eating_style=eating_style,
            allergies=allergies,
            medical_conditions=medical_conditions,
            magic_list=magic_list
        )

        return Response(combo_response, status=status.HTTP_200_OK)


class MyDiningProfileView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema()
    def get(self, request, user_id, profile_name):
        try:
            user = CustomUserModel.objects.filter(id=user_id).first()
        except CustomUserModel.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        
        profile = ProfileModel.objects.filter(user=user, profile_name=profile_name).first()

        if not profile:
            return Response({"error": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)
        


        eating_style = list(profile.eating_style.values_list('eating_style_name', flat=True))
        allergies = list(profile.allergies.values_list('allergy_name', flat=True))
        medical_conditions = list(profile.medical_conditions.values_list('medical_condition_name', flat=True))
        magic_list = profile.magic_list
        
        avoid_list_response = avoid_list_json(
            eating_style=eating_style,
            allergies=allergies,
            medical_conditions=medical_conditions,
            magic_list=magic_list
        )

        return Response(avoid_list_response, status=status.HTTP_200_OK)
    

class DiningProfileView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema()
    def get(self, request, user_id, profile_name):
        try:
            user = CustomUserModel.objects.filter(id=user_id).first()
        except CustomUserModel.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        
        profile = ProfileModel.objects.filter(user=user, profile_name=profile_name).first()

        if not profile:
            return Response({"error": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)
        


        eating_style = list(profile.eating_style.values_list('eating_style_name', flat=True))
        allergies = list(profile.allergies.values_list('allergy_name', flat=True))
        medical_conditions = list(profile.medical_conditions.values_list('medical_condition_name', flat=True))

        
        dining_profile_response = {
            "eating_style": eating_style,
            "allergies": allergies,
            "medical_conditions": medical_conditions,
        }

        return Response(dining_profile_response, status=status.HTTP_200_OK)



class MyOwnPlatterView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema()
    def get(self, request, user_id, profile_id, plate_id):
        try:
            user = CustomUserModel.objects.filter(id=user_id).first()
        except CustomUserModel.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        

        profile = ProfileModel.objects.filter(user=user, id=profile_id).first()

        if not profile:
            return Response({"error": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)
        
        plate = MyPlateModel.objects.filter(user=user, profile=profile, id=plate_id).first()
        if not plate:
            return Response({"error": "MyPlate not found."}, status=status.HTTP_404_NOT_FOUND)
        
    
        return Response({"my_platter": MyPlateSerializer(plate).data}, status=status.HTTP_200_OK)
    


