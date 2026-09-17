from django.contrib.auth import get_user_model
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import ParentProfile, Role, StudentProfile, TeacherProfile
from .permissions import IsAdmin, IsParent, parent_profile_of, user_is_admin
from .serializers import (
    AdminCreateUserSerializer,
    AssignRelationsSerializer,
    ChildSearchResultSerializer,
    LinkChildSerializer,
    ParentProfileSerializer,
    RoleAwareTokenObtainPairSerializer,
    SetGuardianSerializer,
    StudentProfileSerializer,
    TeacherProfileSerializer,
    UserMiniSerializer,
)

User = get_user_model()


class LoginView(TokenObtainPairView):
    """POST {email, password} -> {access, refresh, role, name, student_id?}.
    Works identically for every role; role comes from the DB, never the client."""
    serializer_class = RoleAwareTokenObtainPairSerializer
    throttle_scope = "auth"


class LogoutView(APIView):
    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"detail": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            RefreshToken(refresh_token).blacklist()
        except TokenError:
            return Response(
                {"detail": "Invalid or expired refresh token."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_205_RESET_CONTENT)


class MeView(APIView):
    def get(self, request):
        user = request.user
        data = UserMiniSerializer(user).data
        ctx = {"request": request}
        if user.role == Role.STUDENT and hasattr(user, "student_profile"):
            data["profile"] = StudentProfileSerializer(user.student_profile, context=ctx).data
        elif user.role == Role.TEACHER and hasattr(user, "teacher_profile"):
            data["profile"] = TeacherProfileSerializer(user.teacher_profile, context=ctx).data
        elif user.role == Role.PARENT and hasattr(user, "parent_profile"):
            data["profile"] = ParentProfileSerializer(user.parent_profile, context=ctx).data
        return Response(data)


class AdminUserViewSet(viewsets.ModelViewSet):
    """Full user provisioning/management. Admin only."""
    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = AdminCreateUserSerializer
    permission_classes = [IsAdmin]
    filterset_fields = ["role", "is_active"]


class StudentProfileViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StudentProfileSerializer

    def get_queryset(self):
        user = self.request.user
        qs = StudentProfile.objects.select_related(
            "user", "authorized_parent__user"
        ).prefetch_related("teachers__user")
        if user_is_admin(user):
            return qs
        if user.role == Role.STUDENT:
            return qs.filter(user=user)
        if user.role == Role.PARENT:
            parent = parent_profile_of(user)
            return qs.filter(parents=parent) if parent else qs.none()
        if user.role == Role.TEACHER and hasattr(user, "teacher_profile"):
            return qs.filter(teachers=user.teacher_profile)
        return qs.none()

    @action(detail=True, methods=["patch"], permission_classes=[IsAdmin])
    def set_guardian(self, request, pk=None):
        """Admin-only: authorize a parent (by email and/or existing account)
        to link to this student. This is what LinkChildView checks against -
        without this being set, a parent who finds/guesses a Student ID
        cannot complete a link."""
        student = self.get_object()
        serializer = SetGuardianSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        if "guardian_email" in serializer.validated_data:
            student.guardian_email = serializer.validated_data["guardian_email"]
        if "authorized_parent_id" in serializer.validated_data:
            student.authorized_parent = serializer.validated_data["authorized_parent_id"]
        student.save(update_fields=["guardian_email", "authorized_parent"])
        return Response(StudentProfileSerializer(student, context={"request": request}).data)

    @action(detail=True, methods=["patch"], permission_classes=[IsAdmin])
    def assign_relations(self, request, pk=None):
        """Admin-only: manage a student's ongoing relationships in one call -
        which teachers teach them and (when the parent already has an account)
        a direct, immediate parent link. Any field left out of the request
        body is left unchanged."""
        student = self.get_object()
        serializer = AssignRelationsSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if "teacher_ids" in data:
            student.teachers.set(data["teacher_ids"])

        if "parent_id" in data:
            new_parent = data["parent_id"]
            # Detach from any previously-linked parents so a student always
            # has at most the one parent an admin just explicitly set here
            # (a parent can still have many children - this only bounds
            # this student's side of the relationship).
            for existing_parent in student.parents.all():
                existing_parent.children.remove(student)
            if new_parent is not None:
                new_parent.children.add(student)
                student.authorized_parent = new_parent
            else:
                student.authorized_parent = None
            student.save(update_fields=["authorized_parent"])

        return Response(StudentProfileSerializer(student, context={"request": request}).data)


class TeacherProfileViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TeacherProfileSerializer

    def get_queryset(self):
        user = self.request.user
        qs = TeacherProfile.objects.select_related("user")
        if user_is_admin(user):
            return qs
        if user.role == Role.STUDENT and hasattr(user, "student_profile"):
            return qs.filter(students=user.student_profile)
        return qs.none()


class ParentProfileViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ParentProfileSerializer

    def get_queryset(self):
        user = self.request.user
        qs = ParentProfile.objects.select_related("user").prefetch_related("children__user")
        if user_is_admin(user):
            return qs
        if user.role == Role.PARENT:
            return qs.filter(user=user)
        return qs.none()


class SearchChildView(generics.GenericAPIView):
    """GET /api/accounts/parent/search-child/?student_id=STU-XXXX
    Returns minimal, non-sensitive info only, and finding a student here
    does NOT by itself grant access - LinkChildView (below) separately
    checks that this parent's account was actually pre-authorized for that
    student before the link can complete."""
    permission_classes = [IsParent]
    serializer_class = ChildSearchResultSerializer

    def get(self, request):
        student_id = request.query_params.get("student_id", "").strip()
        if not student_id:
            return Response({"detail": "student_id query param is required."}, status=400)
        try:
            student = StudentProfile.objects.select_related("user").get(student_id=student_id)
        except StudentProfile.DoesNotExist:
            return Response({"detail": "No student found with that Student ID."}, status=404)
        return Response(self.get_serializer(student).data)


class LinkChildView(generics.GenericAPIView):
    """POST {student_id} -> links the searched child to the authenticated
    parent, but ONLY if that student's record already authorizes this
    parent - either `guardian_email` matches this parent's login email, or
    `authorized_parent` points at this parent's account (both set by an
    admin, see StudentProfileViewSet.set_guardian). Knowing/guessing a
    Student ID is no longer sufficient on its own to gain access."""
    permission_classes = [IsParent]
    serializer_class = LinkChildSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        student = serializer.validated_data["student_id"]
        parent = parent_profile_of(request.user)
        parent.children.add(student)
        return Response(
            StudentProfileSerializer(student, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )
