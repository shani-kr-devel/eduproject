from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Role, StudentProfile
from apps.accounts.permissions import can_access_student, parent_profile_of, teacher_profile_of, user_is_admin
from apps.courses.models import Course, CourseAssignment, CourseContentProgress, CourseQuizAttempt, Enrollment

from .models import Feedback, StudentGroup, Test, TestAnswer, TestAssignment, TestAttempt, TestQuestion, TestScore
from .permissions import ReadOnlyIfNotOwnerTeacher
from .serializers import (
    FeedbackSerializer, PerformanceReportSerializer, StudentGroupSerializer,
    TestAnswerSerializer, TestAttemptSerializer, TestQuestionSerializer,
    TestScoreSerializer, TestSerializer,
)


class TestViewSet(viewsets.ModelViewSet):
    serializer_class = TestSerializer
    permission_classes = [IsAuthenticated, ReadOnlyIfNotOwnerTeacher]

    def get_permissions(self):
        if self.action in ("start", "submit"):
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        qs = Test.objects.select_related("teacher__user").prefetch_related(
            "scores__student__user", "questions", "attempts__answers"
        )
        if user_is_admin(user):
            return qs
        if user.role == Role.TEACHER and hasattr(user, "teacher_profile"):
            return qs.filter(teacher=user.teacher_profile)
        if user.role == Role.STUDENT and hasattr(user, "student_profile"):
            return qs.filter(
                Q(group_assignments__group__students=user.student_profile)
                | Q(attempts__student=user.student_profile)
            ).distinct()
        if user.role == Role.PARENT:
            parent = parent_profile_of(user)
            return qs.filter(group_assignments__group__students__parents=parent).distinct() if parent else qs.none()
        return qs.none()

    def perform_create(self, serializer):
        if self.request.user.role != Role.TEACHER:
            raise PermissionDenied("Only teachers can create tests.")
        serializer.save(teacher=teacher_profile_of(self.request.user))

    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        test = self.get_object()
        teacher = teacher_profile_of(request.user)
        if request.user.role != Role.TEACHER or test.teacher_id != teacher.pk:
            raise PermissionDenied("Only the creating teacher can assign this test.")
        groups = StudentGroup.objects.filter(pk__in=request.data.get("group_ids", []), teacher=teacher)
        TestAssignment.objects.bulk_create(
            [TestAssignment(test=test, group=group) for group in groups], ignore_conflicts=True
        )
        return Response(TestSerializer(test, context={"request": request}).data)

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        test = self.get_object()
        student = getattr(request.user, "student_profile", None)
        if request.user.role != Role.STUDENT or not student or not test.group_assignments.filter(group__students=student).exists():
            raise PermissionDenied("This test is not assigned to you.")
        attempt, created = TestAttempt.objects.get_or_create(
            test=test,
            student=student,
            defaults={
                "started_at": timezone.now(),
                "max_score": sum(question.points for question in test.questions.all()),
            },
        )
        if not created and attempt.submitted_at:
            raise ValidationError({"detail": "This test has already been submitted."})
        return Response(TestAttemptSerializer(attempt, context={"request": request}).data)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        test = self.get_object()
        student = getattr(request.user, "student_profile", None)
        if request.user.role != Role.STUDENT or not student:
            raise PermissionDenied("Only students can submit tests.")
        try:
            attempt = TestAttempt.objects.get(test=test, student=student, submitted_at__isnull=True)
        except TestAttempt.DoesNotExist:
            raise ValidationError({"detail": "Start the test before submitting it."})
        submitted_at = timezone.now()
        answers = request.data.get("answers", {})
        score = 0
        for question in test.questions.all():
            answer = str(answers.get(str(question.id), "")).strip()
            is_correct = (
                question.question_type == TestQuestion.QuestionType.MULTIPLE_CHOICE
                and answer.lower() == question.correct_answer.strip().lower()
            )
            points = question.points if is_correct else 0
            TestAnswer.objects.update_or_create(
                attempt=attempt,
                question=question,
                defaults={
                    "answer": answer,
                    "is_correct": is_correct if question.question_type == TestQuestion.QuestionType.MULTIPLE_CHOICE else None,
                    "points_awarded": points,
                },
            )
            score += points
        attempt.submitted_at = submitted_at
        attempt.duration_seconds = max(0, int((submitted_at - attempt.started_at).total_seconds()))
        attempt.score = score
        attempt.save(update_fields=["submitted_at", "duration_seconds", "score"])
        return Response(TestAttemptSerializer(attempt, context={"request": request}).data)


class TestQuestionViewSet(viewsets.ModelViewSet):
    serializer_class = TestQuestionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user_is_admin(user):
            return TestQuestion.objects.all()
        if user.role == Role.TEACHER and hasattr(user, "teacher_profile"):
            return TestQuestion.objects.filter(test__teacher=user.teacher_profile)
        return TestQuestion.objects.none()

    def perform_create(self, serializer):
        if self.request.user.role != Role.TEACHER:
            raise PermissionDenied("Only teachers can create test questions.")
        test = serializer.validated_data["test"]
        if test.teacher_id != teacher_profile_of(self.request.user).pk:
            raise PermissionDenied("You can only edit your own tests.")
        serializer.save()


class StudentGroupViewSet(viewsets.ModelViewSet):
    serializer_class = StudentGroupSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user_is_admin(user):
            return StudentGroup.objects.all()
        if user.role == Role.TEACHER and hasattr(user, "teacher_profile"):
            return StudentGroup.objects.filter(teacher=user.teacher_profile)
        return StudentGroup.objects.none()

    def perform_create(self, serializer):
        if self.request.user.role != Role.TEACHER:
            raise PermissionDenied("Only teachers can create student groups.")
        teacher = teacher_profile_of(self.request.user)
        students = serializer.validated_data.get("students", [])
        if any(not student.teachers.filter(pk=teacher.pk).exists() for student in students):
            raise PermissionDenied("Groups may only contain your students.")
        serializer.save(teacher=teacher)

    def perform_update(self, serializer):
        teacher = teacher_profile_of(self.request.user)
        students = serializer.validated_data.get("students", [])
        if any(not student.teachers.filter(pk=teacher.pk).exists() for student in students):
            raise PermissionDenied("Groups may only contain your students.")
        serializer.save()


class TestAttemptViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = TestAttemptSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = TestAttempt.objects.select_related("test", "student__user").prefetch_related("answers__question")
        if user_is_admin(user):
            return qs
        if user.role == Role.TEACHER and hasattr(user, "teacher_profile"):
            return qs.filter(test__teacher=user.teacher_profile)
        if user.role == Role.STUDENT and hasattr(user, "student_profile"):
            return qs.filter(student=user.student_profile)
        return qs.none()


class TestScoreViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = TestScoreSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = TestScore.objects.select_related("student__user", "test__teacher")
        if user_is_admin(user):
            return qs
        if user.role == Role.TEACHER and hasattr(user, "teacher_profile"):
            return qs.filter(test__teacher=user.teacher_profile)
        if user.role == Role.STUDENT and hasattr(user, "student_profile"):
            return qs.filter(student=user.student_profile)
        return qs.none()


class FeedbackViewSet(viewsets.ModelViewSet):
    serializer_class = FeedbackSerializer
    permission_classes = [IsAuthenticated, ReadOnlyIfNotOwnerTeacher]

    def get_queryset(self):
        user = self.request.user
        qs = Feedback.objects.select_related("student__user", "author_teacher__user")
        if user_is_admin(user):
            return qs
        if user.role == Role.TEACHER and hasattr(user, "teacher_profile"):
            return qs.filter(author_teacher=user.teacher_profile)
        if user.role == Role.STUDENT and hasattr(user, "student_profile"):
            return qs.filter(student=user.student_profile)
        if user.role == Role.PARENT:
            parent = parent_profile_of(user)
            return qs.filter(student__parents=parent) if parent else qs.none()
        return qs.none()

    def perform_create(self, serializer):
        if self.request.user.role != Role.TEACHER:
            raise PermissionDenied("Only teachers can give feedback.")
        teacher = teacher_profile_of(self.request.user)
        student = serializer.validated_data["student"]
        if not student.teachers.filter(pk=teacher.pk).exists():
            raise PermissionDenied("You can only give feedback to your own students.")
        serializer.save(author_teacher=teacher)


class PerformanceReportView(APIView):
    def get(self, request, student_pk):
        student = get_object_or_404(StudentProfile, pk=student_pk)
        if not can_access_student(request.user, student):
            raise PermissionDenied("You do not have access to this student's data.")
        scores = TestAttempt.objects.filter(student=student, submitted_at__isnull=False)
        percentages = [float(attempt.score) / attempt.max_score * 100 for attempt in scores if attempt.max_score]
        test_reports = []
        for attempt in scores.select_related("test").prefetch_related("answers__question"):
            test_reports.append(
                {
                    "id": attempt.id,
                    "test_id": attempt.test_id,
                    "title": attempt.test.title,
                    "subject": attempt.test.subject,
                    "date": attempt.test.date,
                    "score": attempt.score,
                    "max_score": attempt.max_score,
                    "percentage": round(float(attempt.score) / attempt.max_score * 100, 1)
                    if attempt.max_score else None,
                    "duration_seconds": attempt.duration_seconds,
                    "submitted_at": attempt.submitted_at,
                    "answers": [
                        {
                            "question": answer.question.prompt,
                            "answer": answer.answer,
                            "is_correct": answer.is_correct,
                            "points_awarded": answer.points_awarded,
                        }
                        for answer in attempt.answers.all()
                    ],
                }
            )

        course_ids = set(
            Enrollment.objects.filter(student=student).values_list("course_id", flat=True)
        ) | set(
            CourseAssignment.objects.filter(student=student).values_list("course_id", flat=True)
        )
        course_reports = []
        for course in Course.objects.filter(pk__in=course_ids).prefetch_related("contents"):
            quiz_content_ids = list(course.contents.filter(content_type="quiz").values_list("id", flat=True))
            quiz_attempts = list(
                CourseQuizAttempt.objects.filter(
                    student=student, content_id__in=quiz_content_ids
                ).order_by("-submitted_at")
            )
            quiz_percentages = [
                float(attempt.score) / attempt.max_score * 100
                for attempt in quiz_attempts
                if attempt.max_score
            ]
            course_reports.append(
                {
                    "course_id": course.id,
                    "title": course.title,
                    "category": course.category,
                    "total_lessons": course.contents.count(),
                    "video_lessons": course.contents.filter(content_type="video").count(),
                    "completed_lessons": CourseContentProgress.objects.filter(
                        student=student, content__course=course
                    ).count(),
                    "completed_video_lessons": CourseContentProgress.objects.filter(
                        student=student, content__course=course, content__content_type="video"
                    ).count(),
                    "completion_pct": round(
                        CourseContentProgress.objects.filter(
                            student=student, content__course=course
                        ).count() / course.contents.count() * 100,
                        1,
                    ) if course.contents.count() else 0,
                    "quizzes": len(quiz_content_ids),
                    "quizzes_attempted": len(quiz_attempts),
                    "average_quiz_score_pct": round(sum(quiz_percentages) / len(quiz_percentages), 1)
                    if quiz_percentages else None,
                    "last_activity": quiz_attempts[0].submitted_at if quiz_attempts else None,
                }
            )
        recent_feedback = Feedback.objects.filter(student=student).select_related(
            "author_teacher__user"
        )[:10]
        payload = {
            "student": student,
            "average_test_score_pct": round(sum(percentages) / len(percentages), 1) if percentages else None,
            "tests_taken": scores.count(),
            "test_reports": test_reports,
            "course_reports": course_reports,
            "recent_feedback": recent_feedback,
        }
        return Response(PerformanceReportSerializer(payload, context={"request": request}).data)
