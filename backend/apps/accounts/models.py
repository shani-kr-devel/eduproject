import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from .managers import UserManager


class Role(models.TextChoices):
    ADMIN = "admin", "Admin"
    TEACHER = "teacher", "Teacher"
    STUDENT = "student", "Student"
    PARENT = "parent", "Parent"


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user. Email is the login identifier; role drives permissions."""

    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, db_index=True)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "role"]

    class Meta:
        indexes = [models.Index(fields=["role"])]

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name


def generate_student_id():
    """Unique, human-friendly Student ID, e.g. STU-4F2A9C1B."""
    return f"STU-{uuid.uuid4().hex[:8].upper()}"


class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="teacher_profile")
    subject_specialization = models.CharField(max_length=150, blank=True)
    bio = models.TextField(blank=True)

    def __str__(self):
        return self.user.get_full_name()


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")
    student_id = models.CharField(
        max_length=20, unique=True, db_index=True, default=generate_student_id, editable=False
    )
    grade_level = models.CharField(max_length=50, blank=True)
    teachers = models.ManyToManyField(
        TeacherProfile, related_name="students", blank=True
    )
    # Set by Admin/Teacher when the student's record is created (e.g. from
    # the enrollment form / guardian's contact details on file). A parent
    # account can only link to this student if EITHER of the two fields
    # below matches - this is what actually authorizes the link, rather
    # than knowledge of the Student ID alone (which is fine to search with,
    # but was previously sufficient on its own to complete the link too).
    guardian_email = models.EmailField(
        blank=True,
        db_index=True,
        help_text="Parent/guardian email authorized to link to this student "
        "(used when the parent doesn't have an account yet at enrollment time).",
    )
    authorized_parent = models.ForeignKey(
        "ParentProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="authorized_students",
        help_text="Direct link to an existing parent account authorized for this student.",
    )

    class Meta:
        ordering = ["student_id"]
        indexes = [models.Index(fields=["student_id"]), models.Index(fields=["guardian_email"])]

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.student_id})"


class ParentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="parent_profile")
    children = models.ManyToManyField(
        StudentProfile, related_name="parents", blank=True
    )

    def __str__(self):
        return self.user.get_full_name()
