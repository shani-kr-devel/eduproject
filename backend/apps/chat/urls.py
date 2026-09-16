from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("conversations", views.ConversationViewSet, basename="conversations")

urlpatterns = [
    path("contacts/", views.ContactsView.as_view(), name="chat-contacts"),
    path("start/", views.StartConversationView.as_view(), name="chat-start"),
    path("conversations/<int:conversation_id>/messages/", views.MessageListCreateView.as_view(), name="chat-messages"),
    path("", include(router.urls)),
]
