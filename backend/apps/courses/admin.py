from django.contrib import admin

from .models import Course, CourseContent, Enrollment, Order, Payment


class CourseContentInline(admin.TabularInline):
    model = CourseContent
    extra = 1


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "price", "is_published", "created_by"]
    list_filter = ["category", "is_published"]
    search_fields = ["title"]
    inlines = [CourseContentInline]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["order_id", "student", "course", "amount", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["order_id", "student__student_id"]


admin.site.register(Payment)
admin.site.register(Enrollment)
