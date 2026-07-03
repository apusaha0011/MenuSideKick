from django.contrib import admin
from .models import (
    ConversationModel,
    MessageModel,
    MyPlateModel,
    ScannedDocumentModel
)

# Register your models here.
admin.site.register(ConversationModel)
admin.site.register(MessageModel)
admin.site.register(MyPlateModel)
admin.site.register(ScannedDocumentModel)