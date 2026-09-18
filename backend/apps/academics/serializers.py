from rest_framework import serializers

from apps.accounts.models import Role, StudentProfile
from apps.accounts.serializers import StudentProfileSerializer, TeacherProfileSerializer

from .models import Feedback, Homework, StudentGroup, Test, TestAnswer, TestAttempt, TestQuestion, TestScore


class HomeworkSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.user.get_full_name", read_only=True)
    student_id_code = serializers.CharField(source="student.student_id", read_only=True)
    teacher_name = serializers.CharField(source="teacher.user.get_full_name", read_only=True)
    material_file = serializers.FileField(required=False, allow_null=True)
    submission_file = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = Homework
        fields = [
            "id", "teacher", "teacher_name", "student", "student_name", "student_id_code", "title",
            "description", "due_date", "material_type", "material_text", "material_file", "material_url",
            "status", "submission_text", "submission_file", "submitted_at", "created_at",
        ]
        read_only_fields = ["teacher", "student", "status", "submitted_at", "created_at"]

    def validate(self, attrs):
        material_type = attrs.get("material_type", getattr(self.instance, "material_type", Homework.MaterialType.TEXT))
        if material_type == Homework.MaterialType.TEXT and not attrs.get("material_text", getattr(self.instance, "material_text", "")):
            raise serializers.ValidationError({"material_text": "Text homework needs instructions."})
        if material_type == Homework.MaterialType.LINK and not attrs.get("material_url", getattr(self.instance, "material_url", "")):
            raise serializers.ValidationError({"material_url": "Link homework needs a URL."})
        if material_type in (Homework.MaterialType.IMAGE, Homework.MaterialType.PDF, Homework.MaterialType.TEXT_FILE) and not attrs.get(
            "material_file", getattr(self.instance, "material_file", None)
        ):
            raise serializers.ValidationError({"material_file": "Upload the homework file."})
        return attrs


class HomeworkSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Homework
        fields = ["submission_text", "submission_file"]

    def validate(self, attrs):
        if not attrs.get("submission_text") and not attrs.get("submission_file"):
            raise serializers.ValidationError("Submit text or a file.")
        return attrs


class TestScoreSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.user.get_full_name", read_only=True)
    student_id_code = serializers.CharField(source="student.student_id", read_only=True)

    class Meta:
        model = TestScore
        fields = ["id", "test", "student", "student_name", "student_id_code", "score", "graded_by", "graded_at"]
        read_only_fields = ["graded_by", "graded_at"]


class TestSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source="teacher.user.get_full_name", read_only=True)
    scores = TestScoreSerializer(many=True, read_only=True)
    questions = serializers.SerializerMethodField()
    completed_attempt = serializers.SerializerMethodField()

    class Meta:
        model = Test
        fields = [
            "id", "teacher", "teacher_name", "title", "subject", "date", "duration_minutes",
            "max_score", "scores", "questions", "completed_attempt", "created_at",
        ]
        read_only_fields = ["teacher"]

    def get_completed_attempt(self, obj):
        request = self.context.get("request")
        student = getattr(getattr(request, "user", None), "student_profile", None)
        if not student:
            return None
        attempt = next(
            (item for item in obj.attempts.all() if item.student_id == student.id and item.submitted_at),
            None,
        )
        if not attempt:
            return None
        return {
            "id": attempt.id,
            "test": obj.id,
            "submitted_at": attempt.submitted_at,
            "duration_seconds": attempt.duration_seconds,
            "score": attempt.score,
            "max_score": attempt.max_score,
        }

    def get_questions(self, obj):
        request = self.context.get("request")
        if request and request.user.role == Role.STUDENT:
            return TestQuestionSerializer(obj.questions.all(), many=True, context=self.context).data
        return TestQuestionSerializer(obj.questions.all(), many=True, context=self.context).data


class TestQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestQuestion
        fields = ["id", "test", "prompt", "question_type", "options", "correct_answer", "points", "order"]
        extra_kwargs = {"correct_answer": {"write_only": True}}

    def validate(self, attrs):
        if attrs.get("question_type", TestQuestion.QuestionType.MULTIPLE_CHOICE) == TestQuestion.QuestionType.MULTIPLE_CHOICE:
            if len(attrs.get("options", [])) < 2:
                raise serializers.ValidationError({"options": "Multiple-choice questions need at least two options."})
            if attrs.get("correct_answer") not in attrs.get("options", []):
                raise serializers.ValidationError({"correct_answer": "The correct answer must be one of the options."})
        return attrs


class StudentGroupSerializer(serializers.ModelSerializer):
    student_ids = serializers.PrimaryKeyRelatedField(source="students", many=True, read_only=True)
    students = serializers.PrimaryKeyRelatedField(many=True, queryset=StudentProfile.objects.all(), write_only=True, required=False)

    class Meta:
        model = StudentGroup
        fields = ["id", "name", "student_ids", "students"]


class TestAnswerSerializer(serializers.ModelSerializer):
    question_prompt = serializers.CharField(source="question.prompt", read_only=True)
    class Meta:
        model = TestAnswer
        fields = ["id", "question", "question_prompt", "answer", "is_correct", "points_awarded"]
        read_only_fields = ["is_correct", "points_awarded"]


class TestAttemptSerializer(serializers.ModelSerializer):
    answers = TestAnswerSerializer(many=True, read_only=True)
    student_name = serializers.CharField(source="student.user.get_full_name", read_only=True)
    class Meta:
        model = TestAttempt
        fields = ["id", "test", "student", "student_name", "started_at", "submitted_at", "duration_seconds", "score", "max_score", "answers"]
        read_only_fields = ["student", "submitted_at", "duration_seconds", "score", "max_score"]


class FeedbackSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = Feedback
        fields = ["id", "student", "author_teacher", "author_name", "message", "created_at"]
        read_only_fields = ["author_teacher"]

    def get_author_name(self, obj):
        if obj.author_teacher:
            return f"{obj.author_teacher.user.get_full_name()} (Teacher)"
        return "Unknown"


class PerformanceReportSerializer(serializers.Serializer):
    """Read-only aggregate: computed, never stored, so it can't drift from
    the     underlying test records."""
    student = StudentProfileSerializer()
    average_test_score_pct = serializers.FloatField(allow_null=True)
    tests_taken = serializers.IntegerField()
    test_reports = serializers.ListField(child=serializers.DictField())
    course_reports = serializers.ListField(child=serializers.DictField())
    recent_feedback = FeedbackSerializer(many=True)
