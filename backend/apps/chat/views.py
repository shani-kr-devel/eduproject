from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import generics, mixins, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Role
from apps.accounts.permissions import (
    parent_profile_of,
    student_profile_of,
    teacher_profile_of,
)
from apps.accounts.serializers import UserMiniSerializer

from .models import Conversation, Message
from .permissions import can_message
from .serializers import ConversationSerializer, MessageSerializer, StartConversationSerializer

User = get_user_model()


class ContactsView(APIView):
    """GET /api/chat/contacts/ -> the people this user is allowed to start
    a conversation with, derived purely from the DB relationships (never
    from anything the client supplies)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        contacts = []

        if user.role == Role.STUDENT:
            student = student_profile_of(user)
            if student:
                contacts += [t.user for t in student.teachers.all()]

        elif user.role == Role.PARENT:
            parent = parent_profile_of(user)
            if parent:
                for child in parent.children.all():
                    contacts += [t.user for t in child.teachers.all()]

        elif user.role == Role.TEACHER:
            teacher = teacher_profile_of(user)
            if teacher:
                for student in teacher.students.all():
                    contacts.append(student.user)
                    for parent in student.parents.all():
                        contacts.append(parent.user)

        unique = list({c.id: c for c in contacts}.values())
        return Response(UserMiniSerializer(unique, many=True).data)


class ConversationViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(participants=self.request.user).prefetch_related(
            "participants", "messages"
        )


class StartConversationView(generics.GenericAPIView):
    """POST {user_id} -> finds or creates the 1:1 conversation, after
    re-validating the relationship server-side via can_message()."""
    permission_classes = [IsAuthenticated]
    serializer_class = StartConversationSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        other = get_object_or_404(User, pk=serializer.validated_data["user_id"])

        if not can_message(request.user, other):
            raise PermissionDenied("You are not permitted to message this user.")

        existing = (
            Conversation.objects.filter(participants=request.user)
            .filter(participants=other)
            .first()
        )
        if existing:
            return Response(ConversationSerializer(existing).data)

        convo = Conversation.objects.create()
        convo.participants.set([request.user, other])
        return Response(ConversationSerializer(convo).data, status=201)


class MessageListCreateView(generics.ListCreateAPIView):
    """REST fallback / history loader. Real-time delivery happens over the
    WebSocket consumer (see consumers.py); both paths share the same
    membership check so neither can be used to bypass the other."""
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_conversation(self):
        convo = get_object_or_404(Conversation, pk=self.kwargs["conversation_id"])
        if not convo.participants.filter(pk=self.request.user.pk).exists():
            raise PermissionDenied("You are not a participant in this conversation.")
        return convo

    def get_queryset(self):
        return self.get_conversation().messages.select_related("sender")

    def perform_create(self, serializer):
        convo = self.get_conversation()
        serializer.save(conversation=convo, sender=self.request.user)
