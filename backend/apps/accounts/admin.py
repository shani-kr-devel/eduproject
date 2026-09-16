from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import ParentProfile, StudentProfile, TeacherProfile, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["email"]
    list_display = ["email", "first_name", "last_name", "role", "is_active", "is_staff"]
    list_filter = ["role", "is_active", "is_staff"]
    search_fields = ["email", "first_name", "last_name"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "phone", "role")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "last_name", "role", "password1", "password2"),
        }),
    )


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ["student_id", "user", "grade_level", "guardian_email", "authorized_parent"]
    list_filter = ["grade_level"]
    search_fields = [
        "student_id", "user__first_name", "user__last_name", "user__email", "guardian_email",
    ]
    filter_horizontal = ["teachers"]
    autocomplete_fields = ["authorized_parent"]
    fieldsets = (
        (None, {"fields": ("user", "student_id", "grade_level")}),
        ("Assignments", {"fields": ("teachers",)}),
        (
            "Parent linking",
            {
                "fields": ("guardian_email", "authorized_parent"),
                "description": (
                    "A parent account can only link to this student if their "
                    "login email matches Guardian email, or their account is "
                    "set directly as Authorized parent."
                ),
            },
        ),
    )
    readonly_fields = ["student_id"]


@admin.register(ParentProfile)
class ParentProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "children_display"]
    search_fields = ["user__first_name", "user__last_name", "user__email"]
    filter_horizontal = ["children"]

    def children_display(self, obj):
        return ", ".join(c.student_id for c in obj.children.all())

    children_display.short_description = "Linked children"


admin.site.register(TeacherProfile)
