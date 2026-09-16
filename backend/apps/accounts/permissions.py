"""
Centralised, explicit permission classes.

Rule of thumb enforced everywhere in this project:
    NEVER trust an ID coming from the React client. Every queryset is
    filtered server-side from request.user, and every object-level
    permission re-derives ownership from the database.
"""
from rest_framework.permissions import BasePermission

from .models import Role


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == Role.ADMIN)


class IsTeacher(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == Role.TEACHER)


class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == Role.STUDENT)


class IsParent(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == Role.PARENT)



class IsAdminOrReadOnlyForOwnRole(BasePermission):
    """Admins get full access; everyone else is read-only through this permission."""

    def has_permission(self, request, view):
        if request.user and request.user.role == Role.ADMIN:
            return True
        return request.method in ("GET", "HEAD", "OPTIONS")


def user_is_admin(user):
    return user.is_authenticated and (user.role == Role.ADMIN or user.is_superuser)


def student_profile_of(user):
    return getattr(user, "student_profile", None)


def teacher_profile_of(user):
    return getattr(user, "teacher_profile", None)


def parent_profile_of(user):
    return getattr(user, "parent_profile", None)


def can_access_student(user, student_profile):
    """
    Central ownership check reused across academics/chat/courses apps so
    the 'who can see this student's data' rule lives in exactly one place.
    """
    if student_profile is None:
        return False
    if user_is_admin(user):
        return True
    if user.role == Role.STUDENT:
        return student_profile_of(user) == student_profile
    if user.role == Role.PARENT:
        parent = parent_profile_of(user)
        return parent is not None and parent.children.filter(pk=student_profile.pk).exists()
    if user.role == Role.TEACHER:
        teacher = teacher_profile_of(user)
        return teacher is not None and student_profile.teachers.filter(pk=teacher.pk).exists()
    return False
