import uuid

from django.conf import settings
from django.db import models

from apps.accounts.models import StudentProfile, TeacherProfile


class Course(models.Model):
    class Category(models.TextChoices):
        MATH = "math", "Mathematics"
        SCIENCE = "science", "Science"
        LANGUAGE = "language", "Language"
        PROGRAMMING = "programming", "Programming"
        TEST_PREP = "test_prep", "Test Preparation"
        OTHER = "other", "Other"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    thumbnail = models.ImageField(upload_to="course_thumbnails/", blank=True, null=True)
    category = models.CharField(max_length=30, choices=Category.choices, default=Category.OTHER)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_published = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    teachers = models.ManyToManyField(TeacherProfile, related_name="courses", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["is_published", "category"])]

    def __str__(self):
        return self.title


class CourseContent(models.Model):
    class ContentType(models.TextChoices):
        VIDEO = "video", "Video"
        PDF = "pdf", "PDF"
        ARTICLE = "article", "Article"
        QUIZ = "quiz", "Quiz"

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="contents")
    title = models.CharField(max_length=200)
    content_type = models.CharField(max_length=20, choices=ContentType.choices, default=ContentType.VIDEO)
    file = models.FileField(upload_to="course_content/", blank=True, null=True)
    external_url = models.URLField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class CourseQuizQuestion(models.Model):
    class QuestionType(models.TextChoices):
        MULTIPLE_CHOICE = "multiple_choice", "Multiple choice"
        SHORT_ANSWER = "short_answer", "Short answer"

    content = models.ForeignKey(CourseContent, on_delete=models.CASCADE, related_name="questions")
    prompt = models.TextField()
    question_type = models.CharField(max_length=20, choices=QuestionType.choices)
    options = models.JSONField(default=list, blank=True)
    correct_answer = models.TextField(blank=True)
    points = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]


class CourseQuizAttempt(models.Model):
    content = models.ForeignKey(CourseContent, on_delete=models.CASCADE, related_name="attempts")
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="course_quiz_attempts")
    answers = models.JSONField(default=dict)
    score = models.PositiveIntegerField(default=0)
    max_score = models.PositiveIntegerField(default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-submitted_at"]


def generate_order_id():
    return f"ORD-{uuid.uuid4().hex[:12].upper()}"


class Order(models.Model):
    class Status(models.TextChoices):
        CREATED = "created", "Created"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    order_id = models.CharField(max_length=40, unique=True, default=generate_order_id, editable=False)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="orders")
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders")
    course_title = models.CharField(max_length=200, blank=True, default="")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CREATED)
    gateway_order_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status"])]

    def __str__(self):
        return f"{self.order_id} - {self.course_title} - {self.status}"


class Payment(models.Model):
    class Method(models.TextChoices):
        UPI = "upi", "UPI"
        GOOGLE_PAY = "google_pay", "Google Pay"
        PHONEPE = "phonepe", "PhonePe"
        PAYTM = "paytm", "Paytm"
        CARD = "card", "Card"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    payment_id = models.CharField(max_length=100, unique=True)
    method = models.CharField(max_length=20, choices=Method.choices, default=Method.UPI)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    # Never store raw card/UPI credentials - only the gateway's own opaque
    # reference IDs and whatever non-sensitive metadata it returns.
    gateway_response = models.JSONField(default=dict, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.payment_id} ({self.status})"


class Enrollment(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="enrollment")
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "course")

    def __str__(self):
        return f"{self.student.student_id} enrolled in {self.course.title}"


class CourseAssignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="assignments")
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="course_assignments")
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name="course_assignments")
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("course", "student")
        ordering = ["-assigned_at"]


class CourseContentProgress(models.Model):
    content = models.ForeignKey(CourseContent, on_delete=models.CASCADE, related_name="progress_records")
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="course_content_progress")
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("content", "student")
        ordering = ["completed_at"]
