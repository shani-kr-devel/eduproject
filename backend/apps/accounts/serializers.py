from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import ParentProfile, Role, StudentProfile, TeacherProfile
from .permissions import user_is_admin

User = get_user_model()


class RoleAwareTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Adds role + display info to the JWT payload so the frontend can route
    without an extra round trip, while the backend still re-verifies role on
    every request via DRF permissions (the token claims are for UX only)."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["name"] = user.get_full_name()
        if user.role == Role.STUDENT and hasattr(user, "student_profile"):
            token["student_id"] = user.student_profile.student_id
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["role"] = self.user.role
        data["name"] = self.user.get_full_name()
        data["email"] = self.user.email
        if self.user.role == Role.STUDENT and hasattr(self.user, "student_profile"):
            data["student_id"] = self.user.student_profile.student_id
        return data


class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "email", "role"]


class StudentProfileSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)
    teacher_names = serializers.SerializerMethodField()
    authorized_parent_name = serializers.CharField(
        source="authorized_parent.user.get_full_name", read_only=True, default=None
    )

    class Meta:
        model = StudentProfile
        fields = [
            "id", "user", "student_id", "grade_level",
            "teachers", "teacher_names", "guardian_email", "authorized_parent",
            "authorized_parent_name",
        ]
        read_only_fields = ["student_id"]

    def get_teacher_names(self, obj):
        return [t.user.get_full_name() for t in obj.teachers.all()]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # guardian_email/authorized_parent are identity-verification data
        # for the parent-linking flow, not something every viewer needs -
        # only admins (who manage that authorization) see them.
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not (user and getattr(user, "is_authenticated", False) and user_is_admin(user)):
            data.pop("guardian_email", None)
            data.pop("authorized_parent", None)
            data.pop("authorized_parent_name", None)
        return data


class TeacherProfileSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)

    class Meta:
        model = TeacherProfile
        fields = ["id", "user", "subject_specialization", "bio"]


class ParentProfileSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)
    children = StudentProfileSerializer(many=True, read_only=True)

    class Meta:
        model = ParentProfile
        fields = ["id", "user", "children"]


class ParentProvisionSerializer(serializers.Serializer):
    """Parent details submitted with a new student.

    The email is also the parent's account key, so an existing parent can
    be reused for another child without asking them to create a second login.
    """

    email = serializers.EmailField()
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(
        required=False, allow_blank=True, min_length=8, write_only=True
    )


class ChildSearchResultSerializer(serializers.ModelSerializer):
    """Deliberately minimal: shown only *before* a parent has been linked,
    so it must never leak grades/homework/etc."""
    user = UserMiniSerializer(read_only=True)

    class Meta:
        model = StudentProfile
        fields = ["id", "user", "student_id", "grade_level"]


class AdminCreateUserSerializer(serializers.ModelSerializer):
    """Admin-only endpoint to provision accounts for every role.
    Extra role-specific fields are optional and used to also create the
    linked profile in the same transaction."""

    password = serializers.CharField(write_only=True, min_length=8)
    grade_level = serializers.CharField(required=False, allow_blank=True, write_only=True)
    teacher_ids = serializers.PrimaryKeyRelatedField(
        queryset=TeacherProfile.objects.all(), many=True, required=False, write_only=True
    )
    subject_specialization = serializers.CharField(required=False, allow_blank=True, write_only=True)
    parent = ParentProvisionSerializer(required=False, write_only=True)
    # Authorize a parent to link to this student at creation time - either
    # by email (parent may not have an account yet) or by picking an
    # existing parent account directly. Neither is required; an admin can
    # also set/change this later via StudentProfileViewSet.set_guardian.
    guardian_email = serializers.EmailField(required=False, allow_blank=True, write_only=True)
    authorized_parent_id = serializers.PrimaryKeyRelatedField(
        queryset=ParentProfile.objects.all(), required=False, allow_null=True, write_only=True
    )

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "phone", "role", "password",
            "grade_level", "teacher_ids", "subject_specialization",
            "guardian_email", "authorized_parent_id", "parent",
        ]

    def validate(self, attrs):
        parent = attrs.get("parent")
        if parent and attrs.get("role") != Role.STUDENT:
            raise serializers.ValidationError(
                {"parent": "Parent information can only be provided when creating a student."}
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        grade_level = validated_data.pop("grade_level", "")
        teachers = validated_data.pop("teacher_ids", [])
        subject_specialization = validated_data.pop("subject_specialization", "")
        guardian_email = validated_data.pop("guardian_email", "")
        authorized_parent = validated_data.pop("authorized_parent_id", None)
        parent_details = validated_data.pop("parent", None)
        password = validated_data.pop("password")

        user = User(**validated_data)
        user.set_password(password)
        user.save()

        if user.role == Role.STUDENT:
            parent_profile = authorized_parent
            if parent_details:
                parent_email = parent_details["email"].strip()
                parent_user = User.objects.filter(email__iexact=parent_email).first()
                if parent_user:
                    if parent_user.role != Role.PARENT:
                        raise serializers.ValidationError(
                            {"parent": "That email is already used by a non-parent account."}
                        )
                    parent_profile, _ = ParentProfile.objects.get_or_create(user=parent_user)
                else:
                    parent_password = parent_details.get("password", "")
                    if not parent_password:
                        raise serializers.ValidationError(
                            {"parent": {"password": "A password is required for a new parent account."}}
                        )
                    parent_user = User.objects.create_user(
                        email=parent_email,
                        password=parent_password,
                        first_name=parent_details.get("first_name", ""),
                        last_name=parent_details.get("last_name", ""),
                        role=Role.PARENT,
                    )
                    parent_profile = ParentProfile.objects.create(user=parent_user)

            profile = StudentProfile.objects.create(
                user=user,
                grade_level=grade_level,
                guardian_email=guardian_email or (parent_details["email"].strip() if parent_details else ""),
                authorized_parent=parent_profile,
            )
            if teachers:
                profile.teachers.set(teachers)
            if parent_profile:
                parent_profile.children.add(profile)
        elif user.role == Role.TEACHER:
            TeacherProfile.objects.create(user=user, subject_specialization=subject_specialization)
        elif user.role == Role.PARENT:
            ParentProfile.objects.create(user=user)
        return user


class SetGuardianSerializer(serializers.Serializer):
    """Admin-only: set/change which parent is authorized to link to a given
    student, after the student record already exists."""

    guardian_email = serializers.EmailField(required=False, allow_blank=True)
    authorized_parent_id = serializers.PrimaryKeyRelatedField(
        queryset=ParentProfile.objects.all(), required=False, allow_null=True
    )


class AssignRelationsSerializer(serializers.Serializer):
    """Admin-only: the single place that manages a student's ongoing
    relationships - which teachers teach them and which parent account has
    full access to their record. Parent
    assignment here is a DIRECT, immediate link (admin already knows both
    accounts exist) - distinct from the parent-initiated search+link flow,
    which exists for when the parent sets up their own account later and
    needs to attach to a student an admin has already pre-authorized."""

    teacher_ids = serializers.PrimaryKeyRelatedField(
        queryset=TeacherProfile.objects.all(), many=True, required=False
    )
    parent_id = serializers.PrimaryKeyRelatedField(
        queryset=ParentProfile.objects.all(), required=False, allow_null=True
    )


class LinkChildSerializer(serializers.Serializer):
    student_id = serializers.CharField()

    def validate_student_id(self, value):
        try:
            return StudentProfile.objects.get(student_id=value)
        except StudentProfile.DoesNotExist:
            raise serializers.ValidationError("No student found with that Student ID.")

    def validate(self, attrs):
        student = attrs["student_id"]
        requesting_parent_user = self.context["request"].user
        parent_profile = getattr(requesting_parent_user, "parent_profile", None)

        email_matches = bool(student.guardian_email) and (
            student.guardian_email.lower() == requesting_parent_user.email.lower()
        )
        id_matches = student.authorized_parent_id is not None and (
            parent_profile is not None and student.authorized_parent_id == parent_profile.pk
        )

        if not (email_matches or id_matches):
            raise serializers.ValidationError(
                "This account isn't authorized to link to that student. The "
                "school admin needs to register your email or account against "
                "this Student ID before you can link to them."
            )
        return attrs
