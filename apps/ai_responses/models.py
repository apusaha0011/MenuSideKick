from django.db import models
from apps.users.models import CustomUserModel

# Create your models here.
class MyPlateModel(models.Model):
    user = models.ForeignKey(CustomUserModel, on_delete=models.CASCADE, related_name='myplates')
    profile = models.ForeignKey(
        'users.ProfileModel',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='myplates'
    )
    meal_name = models.CharField(max_length=255)
    image_url = models.URLField()
    plate_combo = models.JSONField(default=list, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"MyPlate {self.id} by {self.user.email}"


class ConversationModel(models.Model):
    user = models.ForeignKey(CustomUserModel, on_delete=models.CASCADE, related_name='conversations')
    title = models.CharField(max_length=255, blank=True, null=True)  # maybe auto-generate from first message
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    summary = models.TextField(blank=True, null=True)  # to keep long-term memory

    # new: optional profile that the user used when interacting
    profile = models.ForeignKey(
        'users.ProfileModel',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='profile_conversations'
    )

    def __str__(self):
        return f"Conversation {self.id} by {self.user.email}"


class MessageModel(models.Model):
    SENDER_CHOICES = [('user', 'User'), ('ai', 'AI')]
    
    conversation = models.ForeignKey(ConversationModel, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message {self.id} in Conversation {self.conversation.id} from {self.sender}"


class ScannedDocumentModel(models.Model):
    user = models.ForeignKey(CustomUserModel, on_delete=models.CASCADE, related_name='scanned_documents')
    profile = models.ForeignKey(
        'users.ProfileModel',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='scanned_documents'
    )
    
    file_urls = models.JSONField(default=list, blank=True, null=True)
    extracted_text = models.TextField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    ai_reply = models.JSONField(default=list, blank=True, null=True) 
    def __str__(self):
        return f"Scanned Document {self.id} by {self.user.email}"