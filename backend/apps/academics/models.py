from django.db import models

from apps.accounts.models import StudentProfile, TeacherProfile


class Test(models.Model):
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name="tests_created")
    title = models.CharField(max_length=200)
    subject = models.CharField(max_length=100)
    date = models.DateField()
    max_score = models.PositiveIntegerField(default=100)
    duration_minutes = models.PositiveIntegerField(default=30)
    students = models.ManyToManyField(StudentProfile, related_name="tests", through="TestScore")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.title} ({self.subject})"


class StudentGroup(models.Model):
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name="student_groups")
    name = models.CharField(max_length=100)
    students = models.ManyToManyField(StudentProfile, related_name="student_groups", blank=True)

    class Meta:
        unique_together = ("teacher", "name")
        ordering = ["name"]


class TestQuestion(models.Model):
    class QuestionType(models.TextChoices):
        MULTIPLE_CHOICE = "multiple_choice", "Multiple choice"
        SHORT_ANSWER = "short_answer", "Short answer"

    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="questions")
    prompt = models.TextField()
    question_type = models.CharField(max_length=20, choices=QuestionType.choices, default=QuestionType.MULTIPLE_CHOICE)
    options = models.JSONField(default=list, blank=True)
    correct_answer = models.TextField(blank=True)
    points = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]


class TestAssignment(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="group_assignments")
    group = models.ForeignKey(StudentGroup, on_delete=models.CASCADE, related_name="test_assignments")

    class Meta:
        unique_together = ("test", "group")


class TestAttempt(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="attempts")
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="test_attempts")
    started_at = models.DateTimeField()
    submitted_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    score = models.PositiveIntegerField(default=0)
    max_score = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("test", "student")


class TestAnswer(models.Model):
    attempt = models.ForeignKey(TestAttempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(TestQuestion, on_delete=models.CASCADE, related_name="answers")
    answer = models.TextField(blank=True)
    is_correct = models.BooleanField(null=True)
    points_awarded = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("attempt", "question")


class TestScore(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="scores")
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="test_scores")
    score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    graded_by = models.ForeignKey(TeacherProfile, on_delete=models.SET_NULL, null=True, blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("test", "student")

    def __str__(self):
        return f"{self.student.student_id} - {self.test.title}: {self.score}"


class Feedback(models.Model):
    """Free-form feedback from a Teacher about a Student.
    Students can view but never edit; only the author (or admin) can edit."""
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="feedback_entries")
    author_teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Feedback for {self.student.student_id}"
