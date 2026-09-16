from rest_framework.permissions import BasePermission, SAFE_METHODS

from apps.accounts.permissions import teacher_profile_of, user_is_admin


class ReadOnlyIfNotOwnerTeacher(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user_is_admin(user) or request.method in SAFE_METHODS:
            return True
        if user.role == "teacher":
            teacher = teacher_profile_of(user)
            owner_field = getattr(obj, "teacher_id", None) or getattr(obj, "author_teacher_id", None)
            return teacher is not None and owner_field == teacher.pk
        return False
