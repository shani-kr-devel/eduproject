from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from .models import ParentProfile, Role, StudentProfile, TeacherProfile, User


class AccountRelationshipTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.teacher = TeacherProfile.objects.create(
            user=User.objects.create_user(
                email="teacher@test.com",
                password="pass12345",
                first_name="T",
                role=Role.TEACHER,
            )
        )
        self.student = StudentProfile.objects.create(
            user=User.objects.create_user(
                email="student@test.com",
                password="pass12345",
                first_name="S",
                role=Role.STUDENT,
            )
        )
        self.parent = ParentProfile.objects.create(
            user=User.objects.create_user(
                email="parent@test.com",
                password="pass12345",
                first_name="P",
                role=Role.PARENT,
            )
        )

    def authenticate_admin(self):
        admin = User.objects.create_user(
            email="admin@test.com",
            password="pass12345",
            first_name="A",
            role=Role.ADMIN,
            is_staff=True,
        )
        response = self.client.post(
            reverse("login"),
            {"email": admin.email, "password": "pass12345"},
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    def test_student_profile_has_no_mentor_fields(self):
        self.client.force_authenticate(user=self.student.user)
        response = self.client.get(reverse("students-list"))
        rows = response.data.get("results", response.data)
        self.assertNotIn("mentor", rows[0])

    def test_admin_can_assign_teacher_and_parent(self):
        self.authenticate_admin()
        response = self.client.patch(
            reverse("students-assign-relations", args=[self.student.pk]),
            {"teacher_ids": [self.teacher.pk], "parent_id": self.parent.pk},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.student.refresh_from_db()
        self.assertTrue(self.student.teachers.filter(pk=self.teacher.pk).exists())
        self.assertTrue(self.parent.children.filter(pk=self.student.pk).exists())

    def test_parent_can_link_by_matching_guardian_email(self):
        self.student.guardian_email = self.parent.user.email
        self.student.save(update_fields=["guardian_email"])
        self.client.force_authenticate(user=self.parent.user)
        response = self.client.post(
            reverse("link-child"),
            {"student_id": self.student.student_id},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(self.parent.children.filter(pk=self.student.pk).exists())
