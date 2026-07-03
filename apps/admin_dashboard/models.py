from django.db import models


# # Create your models here.


# ------------------------Settings Models------------------------
class PrivacyPolicyModel(models.Model):
    content = models.TextField(blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)
    # image stored as S3 URL
    image = models.URLField(max_length=2048, blank=True, null=True)

    def __str__(self):
        return f"Privacy Policy (Last Updated: {self.last_updated})"

class TermsAndConditionsModel(models.Model):
    content = models.TextField(blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)
    # image stored as S3 URL
    image = models.URLField(max_length=2048, blank=True, null=True)

    def __str__(self):
        return f"Terms and Conditions (Last Updated: {self.last_updated})"

class AboutUsModel(models.Model):
    content = models.TextField(blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)
    # image stored as S3 URL
    image = models.URLField(max_length=2048, blank=True, null=True)

    def __str__(self):
        return f"About Us (Last Updated: {self.last_updated})"


# ------------------------Category Models------------------------

class EatingStyleModel(models.Model):
    eating_style_name = models.TextField(unique=True, blank=False, null=False) # Changed to TextField to debug varying(100) error
    details = models.TextField(blank=True, null=True)
    # icon stored as S3 URL
    eating_style_icon = models.URLField(max_length=2048, blank=True, null=True)

    def __str__(self):
        return self.eating_style_name

class AllergyModel(models.Model):
    allergy_name = models.CharField(max_length=255, unique=True, blank=False, null=False)
    # icon stored as S3 URL
    allergy_icon = models.URLField(max_length=2048, blank=True, null=True)

    def __str__(self):
        return self.allergy_name

class MedicalConditionModel(models.Model):
    medical_condition_name = models.CharField(max_length=255, unique=True, blank=False, null=False)
    
    medical_description = models.TextField(blank=True, null=True)
    # icon stored as S3 URL
    medical_condition_icon = models.URLField(max_length=2048, blank=True, null=True)

    def __str__(self):
        return self.medical_condition_name


class AvatarModel(models.Model):
    # avatar stored as S3 URL
    avatar_icon = models.URLField(max_length=2048, blank=True, null=True)

    def __str__(self):
        return str(self.avatar_icon)


# -----------------------Feedback Models------------------------
class FeedbackModel(models.Model):
    email = models.EmailField(blank=False, null=False)
    subject = models.CharField(max_length=200, blank=False, null=False)
    message_details = models.TextField(blank=False, null=False)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # fixed attribute name from user_email -> email
        return f"Feedback from {self.email} - {self.subject}"
