"""
Who is allowed to open a conversation with whom.

Allowed role pairs (per spec):
    Teacher <-> Student   (only if that student is assigned to that teacher)
    Teacher <-> Parent    (only if the parent's child is assigned to that teacher)

Admin can view everything (for moderation) but the pairing rules above are
still what gates two non-admin users from messaging each other.
"""
from apps.accounts.models import Role
from apps.accounts.permissions import (
    parent_profile_of,
    student_profile_of,
    teacher_profile_of,
    user_is_admin,
)


def _teacher_student_linked(teacher_profile, student_profile):
    return student_profile is not None and student_profile.teachers.filter(pk=teacher_profile.pk).exists()


def can_message(user_a, user_b):
    if user_a.pk == user_b.pk:
        return False
    if user_is_admin(user_a) or user_is_admin(user_b):
        return True

    roles = {user_a.role, user_b.role}
    by_role = {user_a.role: user_a, user_b.role: user_b}

    if roles == {Role.TEACHER, Role.STUDENT}:
        teacher = teacher_profile_of(by_role[Role.TEACHER])
        student = student_profile_of(by_role[Role.STUDENT])
        return teacher is not None and _teacher_student_linked(teacher, student)

    if roles == {Role.TEACHER, Role.PARENT}:
        teacher = teacher_profile_of(by_role[Role.TEACHER])
        parent = parent_profile_of(by_role[Role.PARENT])
        if teacher is None or parent is None:
            return False
        return any(_teacher_student_linked(teacher, child) for child in parent.children.all())

    return False
