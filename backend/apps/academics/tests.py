from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import Role, StudentProfile, TeacherProfile, User

from .models import StudentGroup, Test, TestAttempt, TestQuestion


class TimedTestFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.teacher_user = User.objects.create_user(
            email="teacher@test.com", password="pass12345", first_name="Teacher", role=Role.TEACHER
        )
        self.teacher = TeacherProfile.objects.create(user=self.teacher_user)
        self.student_user = User.objects.create_user(
            email="student@test.com", password="pass12345", first_name="Student", role=Role.STUDENT
        )
        self.student = StudentProfile.objects.create(user=self.student_user)
        self.student.teachers.add(self.teacher)
        self.teacher_token = self.client.post(
            reverse("login"), {"email": "teacher@test.com", "password": "pass12345"}
        ).data["access"]

    def test_teacher_can_create_group_and_timed_mcq_test(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.teacher_token}")
        group = self.client.post(
            reverse("student-groups-list"),
            {"name": "Group 1", "students": [self.student.pk]},
            format="json",
        )
        self.assertEqual(group.status_code, 201)
        test = self.client.post(
            reverse("tests-list"),
            {"title": "Algebra", "subject": "Math", "date": "2026-09-20", "duration_minutes": 10},
            format="json",
        )
        self.assertEqual(test.status_code, 201)
        question = self.client.post(
            reverse("test-questions-list"),
            {
                "test": test.data["id"],
                "prompt": "2 + 2?",
                "question_type": "multiple_choice",
                "options": ["3", "4"],
                "correct_answer": "4",
                "points": 2,
            },
            format="json",
        )
        self.assertEqual(question.status_code, 201)
        assignment = self.client.post(
            reverse("tests-assign", args=[test.data["id"]]),
            {"group_ids": [group.data["id"]]},
            format="json",
        )
        self.assertEqual(assignment.status_code, 200)

    def test_student_submission_records_time_and_each_answer(self):
        group = StudentGroup.objects.create(teacher=self.teacher, name="Group 1")
        group.students.add(self.student)
        test = Test.objects.create(
            teacher=self.teacher, title="Algebra", subject="Math", date="2026-09-20", duration_minutes=10
        )
        from .models import TestAssignment
        TestAssignment.objects.create(test=test, group=group)
        question = TestQuestion.objects.create(
            test=test, prompt="2 + 2?", options=["3", "4"], correct_answer="4", points=2
        )
        token = self.client.post(
            reverse("login"), {"email": "student@test.com", "password": "pass12345"}
        ).data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        start = self.client.post(reverse("tests-start", args=[test.pk]))
        self.assertEqual(start.status_code, 200)
        submit = self.client.post(
            reverse("tests-submit", args=[test.pk]), {"answers": {str(question.pk): "4"}}, format="json"
        )
        self.assertEqual(submit.status_code, 200)
        attempt = TestAttempt.objects.get(test=test, student=self.student)
        self.assertIsNotNone(attempt.submitted_at)
        self.assertEqual(attempt.score, 2)
        self.assertEqual(attempt.answers.count(), 1)
