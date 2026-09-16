from rest_framework import serializers

from apps.accounts.models import TeacherProfile

from .models import (
    Course, CourseAssignment, CourseContent, CourseContentProgress, CourseQuizAttempt, CourseQuizQuestion,
    Enrollment, Order, Payment,
)


class CourseQuizQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseQuizQuestion
        fields = ["id", "content", "prompt", "question_type", "options", "correct_answer", "points", "order"]
        extra_kwargs = {"correct_answer": {"write_only": True}}


class CourseQuizAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseQuizAttempt
        fields = ["id", "content", "answers", "score", "max_score", "submitted_at"]
        read_only_fields = ["score", "max_score", "submitted_at"]


class CourseContentSerializer(serializers.ModelSerializer):
    questions = CourseQuizQuestionSerializer(many=True, read_only=True)
    is_completed = serializers.SerializerMethodField()

    def get_is_completed(self, obj):
        request = self.context.get("request")
        student = getattr(getattr(request, "user", None), "student_profile", None)
        return bool(student and obj.progress_records.filter(student=student).exists())

    class Meta:
        model = CourseContent
        fields = ["id", "course", "title", "content_type", "file", "external_url", "order", "questions", "is_completed"]


class CourseSerializer(serializers.ModelSerializer):
    contents = CourseContentSerializer(many=True, read_only=True)
    is_enrolled = serializers.SerializerMethodField()
    teacher_ids = serializers.PrimaryKeyRelatedField(
        source="teachers", many=True, queryset=TeacherProfile.objects.all(),
        required=False, write_only=True,
    )

    class Meta:
        model = Course
        fields = [
            "id", "title", "description", "thumbnail", "category", "price",
            "is_published", "created_by", "created_at", "updated_at", "contents", "is_enrolled",
            "teacher_ids",
        ]
        read_only_fields = ["created_by"]

    def get_is_enrolled(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not hasattr(user, "student_profile"):
            return False
        return obj.enrollments.filter(student=user.student_profile).exists() or obj.assignments.filter(
            student=user.student_profile
        ).exists()


class CourseBrowseSerializer(serializers.ModelSerializer):
    """Public/browse view for students: never includes locked content."""
    is_enrolled = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ["id", "title", "description", "thumbnail", "category", "price", "is_enrolled"]

    def get_is_enrolled(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not hasattr(user, "student_profile"):
            return False
        return (
            obj.enrollments.filter(student=user.student_profile).exists()
            or obj.assignments.filter(student=user.student_profile).exists()
        )


class OrderSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source="course.title", read_only=True)
    student_id_code = serializers.CharField(source="student.student_id", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "order_id", "student", "student_id_code", "course", "course_title",
            "amount", "status", "gateway_order_id", "created_at",
        ]
        read_only_fields = ["order_id", "student", "amount", "status", "gateway_order_id"]


class CheckoutSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "order", "payment_id", "method", "status", "amount", "verified_at", "created_at"]
        read_only_fields = fields


class ConfirmPaymentSerializer(serializers.Serializer):
    """Client-side confirmation right after the checkout widget closes.
    This is a *hint* that speeds up the UI - the webhook is what actually
    marks the order paid and creates the enrollment, so a forged/omitted
    call here can never buy a course for free."""
    order_id = serializers.CharField()
    method = serializers.ChoiceField(choices=Payment.Method.choices, default=Payment.Method.UPI)
    gateway_payment_id = serializers.CharField(required=False, allow_blank=True)
    razorpay_payment_id = serializers.CharField(required=False, allow_blank=True)
    razorpay_signature = serializers.CharField(required=False, allow_blank=True)
    mock_payment_id = serializers.CharField(required=False, allow_blank=True)


class EnrollmentSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)
    student_id_code = serializers.CharField(source="student.student_id", read_only=True)

    class Meta:
        model = Enrollment
        fields = ["id", "student", "student_id_code", "course", "order", "enrolled_at"]


class CourseAssignmentSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)
    course_id = serializers.PrimaryKeyRelatedField(
        source="course", queryset=Course.objects.all(), write_only=True
    )
    course_title = serializers.CharField(source="course.title", read_only=True)
    student_name = serializers.CharField(source="student.user.get_full_name", read_only=True)
    teacher_name = serializers.CharField(source="teacher.user.get_full_name", read_only=True)

    class Meta:
        model = CourseAssignment
        fields = ["id", "course", "course_id", "course_title", "student", "student_name", "teacher", "teacher_name", "assigned_at"]
        read_only_fields = ["teacher"]
