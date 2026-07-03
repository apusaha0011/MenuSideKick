from django.urls import path, include
from .views import (
    MagicListView, 
    ChatView,
    ConversationListView, 
    ConversationMessagesView, 
    ConversationDeleteView,
    MyOwnPlatterView,
    MyDiningProfileView,
    SummaryAutoView,
    OCRView,
    ScannedDocumentViewSet,
    MyPlateListCreateView,
    MyPlateDetailView,
    NewConversationView,
    ComboView,
    DiningProfileView,
)

from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(r'ocr/scanned-documents', ScannedDocumentViewSet, basename='scanned-document')


urlpatterns = [
    path('', include(router.urls)),
    
    # MyPlate endpoints
    path('myplate/', MyPlateListCreateView.as_view(), name='myplate-list-create'),
    path('myplate/<int:pk>/', MyPlateDetailView.as_view(), name='myplate-detail'),
    

    path('magic-list/', MagicListView.as_view(), name='magic-list'),
    path('combo/<int:user_id>/<str:profile_name>/', ComboView.as_view(), name='combo'),
    path('platter/<int:user_id>/<str:profile_name>/', MyDiningProfileView.as_view(), name='platter'),
    path('dining-profile/<int:user_id>/<str:profile_name>/', DiningProfileView.as_view(), name='dining-profile'),
    path('myplate/<int:user_id>/<int:profile_id>/<int:plate_id>/', MyOwnPlatterView.as_view(), name='myplate-user-profile'),


    path('chat/conversations/', ConversationListView.as_view(), name='chat-conversations-list'),
    path('chat/conversations/new/', NewConversationView.as_view(), name='chat-new-conversation'),
    path('chat/conversations/<int:pk>/messages/', ConversationMessagesView.as_view(), name='chat-conversation-messages'),
    path('chat/conversations/<int:pk>/delete/', ConversationDeleteView.as_view(), name='chat-conversation-delete'),
    path('chat/summary/auto/', SummaryAutoView.as_view(), name='chat-summary-auto'),
    path('chat/', ChatView.as_view(), name='chat'),

    # OCR endpoint
    path('ocr/scan/', OCRView.as_view(), name='ocr'), 
]