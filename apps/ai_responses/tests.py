from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from apps.users.models import CustomUserModel, ProfileModel
from apps.ai_responses.models import ScannedDocumentModel
import json

class OCRViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = CustomUserModel.objects.create_user(
            email='testuser@example.com',
            password='password123',
            language='en'
        )
        self.client.force_authenticate(user=self.user)
        self.profile = ProfileModel.objects.create(
            user=self.user,
            profile_name='Test Profile',
            is_active=True
        )
        self.url = reverse('ocr')

    @patch('apps.ai_responses.views.upload_file_to_s3')
    @patch('apps.ai_responses.views.boto3.client')
    @patch('apps.ai_responses.views.generate_ocr_analysis')
    def test_ocr_upload_success(self, mock_ocr_analysis, mock_boto_client, mock_upload_s3):
        # Mock S3 upload
        mock_upload_s3.return_value = ('https://s3.amazonaws.com/bucket/file.pdf', 'file.pdf')
        
        # Mock Textract response
        mock_textract = MagicMock()
        mock_textract.analyze_document.return_value = {
            'Blocks': [
                {'BlockType': 'LINE', 'Text': 'Sample Menu Item'},
            ]
        }
        mock_boto_client.return_value = mock_textract
        
        # Mock AI analysis
        mock_ocr_analysis.return_value = {
            'document_title': 'Test Menu',
            'food_items': [{'food_title': 'Sample Menu Item', 'food_mark': 'safe'}]
        }

        with open('manage.py', 'rb') as f:  # Just any file as a placeholder
            response = self.client.post(self.url, {'files': f}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['document_title'], 'Test Menu')
        
        # Verify database entry
        scanned_doc = ScannedDocumentModel.objects.last()
        self.assertIsNotNone(scanned_doc)
        self.assertEqual(scanned_doc.profile, self.profile)
        self.assertIn('https://s3.amazonaws.com/bucket/file.pdf', scanned_doc.file_urls)

    def test_ocr_upload_no_profile(self):
        # Deactivate profile
        self.profile.is_active = False
        self.profile.save()

        with open('manage.py', 'rb') as f:
            response = self.client.post(self.url, {'files': f}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('No active profile found', response.data['error'])

    def test_ocr_upload_no_files(self):
        response = self.client.post(self.url, {}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('No files were uploaded', response.data['error'])
