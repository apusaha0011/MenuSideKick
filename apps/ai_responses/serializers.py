from rest_framework import serializers
from .models import ConversationModel, MessageModel, ScannedDocumentModel, MyPlateModel


#----------------------------My Plate Serializers ----------------------------
class MyPlateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyPlateModel
        fields = '__all__'
        # user and profile are assigned server-side (active user/profile)
        read_only_fields = ['id', 'user', 'profile', 'created_at', 'updated_at']


class EatingStyleOptionSerializer(serializers.Serializer):
    name = serializers.CharField()
    strict_level = serializers.ChoiceField(
        choices=['Flexible', 'Balanced', 'Strict'],
        default='Balanced'
    )


class MagicListRequestSerializer(serializers.Serializer):
    eating_style = serializers.ListField(
        child=EatingStyleOptionSerializer(),
        required=False,
        default=list
    )
    allergies = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    medical_conditions = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageModel
        fields = ['id', 'conversation', 'content', 'sender', 'created_at']
        read_only_fields = ['id', 'created_at', 'conversation', 'sender']


class ProfileInfoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    profile_name = serializers.CharField()


class ConversationSerializer(serializers.ModelSerializer):
    messages = serializers.SerializerMethodField()
    profile = ProfileInfoSerializer(read_only=True)

    class Meta:
        model = ConversationModel
        fields = ['id', 'title', 'summary', 'created_at', 'updated_at', 'profile', 'messages']

    def get_messages(self, obj):
        qs = obj.messages.order_by('created_at')
        return MessageSerializer(qs, many=True, context=self.context).data


class ChatRequestSerializer(serializers.Serializer):
    conversation_id = serializers.IntegerField(required=False, allow_null=True)
    message = serializers.CharField()




class ScannedDocumentSerializer(serializers.ModelSerializer):
    uploaded_at = serializers.SerializerMethodField()

    class Meta:
        model = ScannedDocumentModel
        fields = ['id', 'user', 'profile', 'file_urls', 'extracted_text', 'uploaded_at', 'ai_reply']
        read_only_fields = ['id', 'user', 'profile', 'file_urls', 'extracted_text', 'uploaded_at', 'ai_reply']
    
    def get_uploaded_at(self, obj):
        """Format the date as 'MMM DD, HH:MM AM/PM'"""
        return obj.uploaded_at.strftime("%b %d, %I:%M %p")