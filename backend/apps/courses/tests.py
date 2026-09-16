import hashlib
import hmac
import json

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import Role, StudentProfile, TeacherProfile, User

from .models import Course, CourseAssignment, CourseContent, Enrollment, Order


@override_settings(PAYMENT_GATEWAY="mock")
class CheckoutFlowTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.student_user = User.objects.create_user(
            email="buyer@test.com", password="pass12345", first_name="Buyer", role=Role.STUDENT
        )
        self.student = StudentProfile.objects.create(user=self.student_user)
        self.course = Course.objects.create(title="Algebra 101", price=500, is_published=True)

        resp = self.client.post(reverse("login"), {"email": "buyer@test.com", "password": "pass12345"})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")

    def test_full_purchase_flow_creates_enrollment_only_after_webhook(self):
        checkout = self.client.post(reverse("checkout"), {"course_id": self.course.id}, format="json")
        self.assertEqual(checkout.status_code, 201)
        order_id = checkout.data["order"]["order_id"]
        gateway_order_id = checkout.data["order"]["gateway_order_id"]

        # Not enrolled yet - only an Order exists.
        self.assertFalse(Enrollment.objects.filter(student=self.student, course=self.course).exists())

        # Simulate the gateway's signed webhook call.
        body = json.dumps({"order_id": gateway_order_id, "payment_id": "mock_pay_123", "status": "success"}).encode()
        signature = hmac.new(b"mock-secret", body, hashlib.sha256).hexdigest()
        webhook_resp = self.client.post(
            reverse("payment-webhook"), data=body, content_type="application/json",
            HTTP_X_WEBHOOK_SIGNATURE=signature,
        )
        self.assertEqual(webhook_resp.status_code, 200)

        order = Order.objects.get(order_id=order_id)
        self.assertEqual(order.status, Order.Status.PAID)
        self.assertTrue(Enrollment.objects.filter(student=self.student, course=self.course).exists())

    def test_webhook_rejects_bad_signature(self):
        checkout = self.client.post(reverse("checkout"), {"course_id": self.course.id}, format="json")
        gateway_order_id = checkout.data["order"]["gateway_order_id"]
        body = json.dumps({"order_id": gateway_order_id, "status": "success"}).encode()
        resp = self.client.post(
            reverse("payment-webhook"), data=body, content_type="application/json",
            HTTP_X_WEBHOOK_SIGNATURE="not-a-real-signature",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(Enrollment.objects.filter(student=self.student, course=self.course).exists())

    def test_cannot_checkout_unpublished_course(self):
        hidden = Course.objects.create(title="Hidden", price=10, is_published=False)
        resp = self.client.post(reverse("checkout"), {"course_id": hidden.id}, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_simulate_mock_payment_enrolls_student(self):
        checkout = self.client.post(reverse("checkout"), {"course_id": self.course.id}, format="json")
        order_id = checkout.data["order"]["order_id"]
        resp = self.client.post(reverse("simulate-mock-payment"), {"order_id": order_id}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Enrollment.objects.filter(student=self.student, course=self.course).exists())
        order = Order.objects.get(order_id=order_id)
        self.assertEqual(order.status, Order.Status.PAID)

    def test_simulate_mock_payment_rejects_other_students_order(self):
        checkout = self.client.post(reverse("checkout"), {"course_id": self.course.id}, format="json")
        order_id = checkout.data["order"]["order_id"]

        other_user = User.objects.create_user(
            email="other@test.com", password="pass12345", first_name="Other", role=Role.STUDENT
        )
        StudentProfile.objects.create(user=other_user)
        login = self.client.post(reverse("login"), {"email": "other@test.com", "password": "pass12345"})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

        resp = self.client.post(reverse("simulate-mock-payment"), {"order_id": order_id}, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_assigned_student_can_retrieve_course_lessons(self):
        teacher_user = User.objects.create_user(
            email="teacher-course@test.com",
            password="pass12345",
            first_name="Teacher",
            role=Role.TEACHER,
        )
        teacher = TeacherProfile.objects.create(user=teacher_user)
        self.student.teachers.add(teacher)
        self.course.teachers.add(teacher)
        lesson = CourseContent.objects.create(
            course=self.course,
            title="Introduction video",
            content_type=CourseContent.ContentType.VIDEO,
            external_url="https://cdn.example.test/intro.mp4",
        )
        CourseAssignment.objects.create(
            course=self.course,
            student=self.student,
            teacher=teacher,
        )

        response = self.client.get(reverse("courses-detail", args=[self.course.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["is_enrolled"])
        self.assertEqual(response.data["contents"][0]["id"], lesson.id)

        content_response = self.client.get(reverse("course-content-list"))
        self.assertEqual(content_response.status_code, 200)
        rows = content_response.data.get("results", content_response.data)
        self.assertEqual(rows[0]["id"], lesson.id)
