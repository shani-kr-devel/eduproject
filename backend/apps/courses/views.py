import csv
import io
import json
import logging

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Role, StudentProfile
from apps.accounts.permissions import IsAdmin, parent_profile_of, teacher_profile_of, user_is_admin

from .models import Course, CourseAssignment, CourseContent, CourseContentProgress, CourseQuizAttempt, CourseQuizQuestion, Enrollment, Order, Payment
from .payments import get_gateway
from .serializers import (
    CheckoutSerializer,
    ConfirmPaymentSerializer,
    CourseBrowseSerializer,
    CourseContentSerializer,
    CourseAssignmentSerializer,
    CourseQuizAttemptSerializer,
    CourseQuizQuestionSerializer,
    CourseSerializer,
    EnrollmentSerializer,
    OrderSerializer,
    PaymentSerializer,
)

logger = logging.getLogger(__name__)


class CourseViewSet(viewsets.ModelViewSet):
    """
    Admin: full CRUD (create/edit/delete/publish, view all purchases via
    /orders/). Everyone else: read-only, and only published courses.
    """
    serializer_class = CourseSerializer
    filterset_fields = ["category", "is_published"]

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy", "publish", "unpublish"):
            return [IsAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = Course.objects.select_related("created_by").prefetch_related("contents")
        if self.request.user.is_authenticated and user_is_admin(self.request.user):
            return qs
        if self.request.user.role == Role.TEACHER and hasattr(self.request.user, "teacher_profile"):
            return qs.filter(teachers=self.request.user.teacher_profile)
        return qs.filter(is_published=True)

    def get_serializer_class(self):
        if self.request.user.is_authenticated and user_is_admin(self.request.user):
            return CourseSerializer
        if self.request.user.role == Role.TEACHER:
            return CourseSerializer
        if self.action == "list":
            return CourseBrowseSerializer
        return CourseSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        course = self.get_object()
        course.is_published = True
        course.save(update_fields=["is_published"])
        return Response(CourseSerializer(course, context={"request": request}).data)

    @action(detail=True, methods=["post"])
    def unpublish(self, request, pk=None):
        course = self.get_object()
        course.is_published = False
        course.save(update_fields=["is_published"])
        return Response(CourseSerializer(course, context={"request": request}).data)

    @action(detail=True, methods=["get"])
    def purchases(self, request, pk=None):
        """Admin: view purchases for a specific course."""
        if not user_is_admin(request.user):
            raise PermissionDenied("Admin only.")
        course = self.get_object()
        orders = Order.objects.filter(course=course).select_related("student__user")
        return Response(OrderSerializer(orders, many=True).data)


class CourseContentViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Locked content: visible only to admins and students enrolled in the
    parent course. Never trust a course_id filter from the client without
    this check."""
    serializer_class = CourseContentSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAuthenticated()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        qs = CourseContent.objects.select_related("course")
        if user_is_admin(user):
            return qs
        if user.role == Role.TEACHER and hasattr(user, "teacher_profile"):
            return qs.filter(course__teachers=user.teacher_profile)
        if hasattr(user, "student_profile"):
            enrolled_course_ids = Enrollment.objects.filter(student=user.student_profile).values_list("course_id", flat=True)
            assigned_course_ids = CourseAssignment.objects.filter(student=user.student_profile).values_list("course_id", flat=True)
            return qs.filter(Q(course_id__in=enrolled_course_ids) | Q(course_id__in=assigned_course_ids))
        return qs.none()

    def perform_create(self, serializer):
        if user_is_admin(self.request.user):
            serializer.save()
            return
        if self.request.user.role != Role.TEACHER:
            raise PermissionDenied("Only teachers can add course content.")
        teacher = teacher_profile_of(self.request.user)
        course = serializer.validated_data["course"]
        if not course.teachers.filter(pk=teacher.pk).exists():
            raise PermissionDenied("You can only add content to courses assigned to you.")
        serializer.save()

    @action(detail=True, methods=["post"], url_path="import-questions")
    def import_questions(self, request, pk=None):
        content = self.get_object()
        if content.content_type != CourseContent.ContentType.QUIZ:
            raise ValidationError({"detail": "Questions can only be imported into quiz content."})
        if not user_is_admin(request.user):
            if request.user.role != Role.TEACHER or not content.course.teachers.filter(
                pk=teacher_profile_of(request.user).pk
            ).exists():
                raise PermissionDenied("You can only import questions into your assigned courses.")

        uploaded = request.FILES.get("file")
        if not uploaded:
            raise ValidationError({"file": "Upload a CSV or JSON question file."})
        raw = uploaded.read().decode("utf-8-sig")
        try:
            if uploaded.name.lower().endswith(".json"):
                rows = json.loads(raw)
            else:
                rows = list(csv.DictReader(io.StringIO(raw)))
        except (UnicodeDecodeError, json.JSONDecodeError, csv.Error) as exc:
            raise ValidationError({"file": f"Could not read the question file: {exc}"})
        if not isinstance(rows, list):
            raise ValidationError({"file": "JSON must contain an array of question objects."})

        created = []
        for index, row in enumerate(rows):
            options = row.get("options", [])
            if isinstance(options, str):
                options = [option.strip() for option in options.split("|") if option.strip()]
            question_type = row.get("question_type", "multiple_choice")
            if question_type == "multiple_choice" and (
                len(options) < 2 or row.get("correct_answer") not in options
            ):
                raise ValidationError(
                    {"file": f"Question {index + 1} needs options and a matching correct_answer."}
                )
            created.append(
                CourseQuizQuestion(
                    content=content,
                    prompt=row.get("prompt", "").strip(),
                    question_type=question_type,
                    options=options,
                    correct_answer=row.get("correct_answer", "").strip(),
                    points=int(row.get("points", 1)),
                    order=int(row.get("order", index)),
                )
            )
        if not all(question.prompt for question in created):
            raise ValidationError({"file": "Every question needs a prompt."})
        CourseQuizQuestion.objects.bulk_create(created)
        return Response({"created": len(created)}, status=status.HTTP_201_CREATED)

    def perform_update(self, serializer):
        user = self.request.user
        course = serializer.instance.course
        if not user_is_admin(user) and (
            user.role != Role.TEACHER
            or not course.teachers.filter(pk=teacher_profile_of(user).pk).exists()
        ):
            raise PermissionDenied("You can only edit content in your assigned courses.")
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        if not user_is_admin(user) and (
            user.role != Role.TEACHER
            or not instance.course.teachers.filter(pk=teacher_profile_of(user).pk).exists()
        ):
            raise PermissionDenied("You can only remove content from your assigned courses.")
        instance.delete()

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        if request.user.role != Role.STUDENT or not hasattr(request.user, "student_profile"):
            raise PermissionDenied("Only students can complete course lessons.")
        content = self.get_object()
        student = request.user.student_profile
        allowed = (
            Enrollment.objects.filter(course=content.course, student=student).exists()
            or CourseAssignment.objects.filter(course=content.course, student=student).exists()
        )
        if not allowed:
            raise PermissionDenied("You do not have access to this lesson.")
        progress, _ = CourseContentProgress.objects.get_or_create(content=content, student=student)
        return Response({"content": content.id, "completed": True, "completed_at": progress.completed_at})


class CourseQuizQuestionViewSet(viewsets.ModelViewSet):
    serializer_class = CourseQuizQuestionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = CourseQuizQuestion.objects.select_related("content__course")
        if user_is_admin(user):
            return qs
        if user.role == Role.TEACHER and hasattr(user, "teacher_profile"):
            return qs.filter(content__course__teachers=user.teacher_profile)
        if user.role == Role.STUDENT and hasattr(user, "student_profile"):
            return qs.filter(content__course__enrollments__student=user.student_profile)
        return qs.none()

    def perform_create(self, serializer):
        if not user_is_admin(self.request.user) and self.request.user.role != Role.TEACHER:
            raise PermissionDenied("Only teachers can design course questions.")
        if user_is_admin(self.request.user):
            serializer.save()
            return
        teacher = teacher_profile_of(self.request.user)
        content = serializer.validated_data["content"]
        if content.content_type != CourseContent.ContentType.QUIZ or not content.course.teachers.filter(pk=teacher.pk).exists():
            raise PermissionDenied("You can only add quiz questions to your assigned course quizzes.")
        serializer.save()

    def perform_update(self, serializer):
        if user_is_admin(self.request.user):
            serializer.save()
            return
        if self.request.user.role != Role.TEACHER:
            raise PermissionDenied("Only teachers can edit course questions.")
        teacher = teacher_profile_of(self.request.user)
        if not serializer.instance.content.course.teachers.filter(pk=teacher.pk).exists():
            raise PermissionDenied("You can only edit questions in your assigned courses.")
        serializer.save()


class CourseQuizAttemptViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = CourseQuizAttemptSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if hasattr(self.request.user, "student_profile"):
            return CourseQuizAttempt.objects.filter(student=self.request.user.student_profile)
        return CourseQuizAttempt.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if user.role != Role.STUDENT or not hasattr(user, "student_profile"):
            raise PermissionDenied("Only students can submit quiz answers.")
        content = serializer.validated_data["content"]
        enrolled = Enrollment.objects.filter(course=content.course, student=user.student_profile).exists()
        assigned = CourseAssignment.objects.filter(course=content.course, student=user.student_profile).exists()
        if content.content_type != CourseContent.ContentType.QUIZ or not (enrolled or assigned):
            raise PermissionDenied("You do not have access to this quiz.")
        questions = list(content.questions.all())
        answers = serializer.validated_data["answers"]
        score = sum(
            question.points
            for question in questions
            if question.question_type == CourseQuizQuestion.QuestionType.MULTIPLE_CHOICE
            and str(answers.get(str(question.id), "")).strip().lower() == question.correct_answer.strip().lower()
        )
        serializer.save(student=user.student_profile, score=score, max_score=sum(q.points for q in questions))
        CourseContentProgress.objects.get_or_create(content=content, student=user.student_profile)


class CourseAssignmentViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = CourseAssignmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = CourseAssignment.objects.select_related("course", "student__user", "teacher__user")
        if user_is_admin(user):
            return qs
        if user.role == Role.TEACHER and hasattr(user, "teacher_profile"):
            return qs.filter(teacher=user.teacher_profile)
        if user.role == Role.STUDENT and hasattr(user, "student_profile"):
            return qs.filter(student=user.student_profile)
        if user.role == Role.PARENT:
            parent = parent_profile_of(user)
            return qs.filter(student__parents=parent) if parent else qs.none()
        return qs.none()

    def perform_create(self, serializer):
        if self.request.user.role != Role.TEACHER:
            raise PermissionDenied("Only teachers can assign courses.")
        teacher = teacher_profile_of(self.request.user)
        course = serializer.validated_data["course"]
        student = serializer.validated_data["student"]
        if not course.teachers.filter(pk=teacher.pk).exists() or not student.teachers.filter(pk=teacher.pk).exists():
            raise PermissionDenied("You can only assign your courses to your students.")
        serializer.save(teacher=teacher)


class CheckoutView(generics.GenericAPIView):
    """POST {course_id} -> creates an Order + gateway order, returns
    whatever the frontend checkout widget needs to open (works identically
    whether the active gateway is the mock or Razorpay)."""
    permission_classes = [IsAuthenticated]
    serializer_class = CheckoutSerializer
    throttle_scope = "payments"

    def post(self, request):
        if request.user.role != Role.STUDENT or not hasattr(request.user, "student_profile"):
            raise PermissionDenied("Only students can purchase courses.")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            course = Course.objects.get(pk=serializer.validated_data["course_id"], is_published=True)
        except Course.DoesNotExist:
            raise ValidationError({"course_id": "Course not found or not published."})

        student = request.user.student_profile
        if Enrollment.objects.filter(student=student, course=course).exists():
            raise ValidationError({"detail": "You are already enrolled in this course."})

        with transaction.atomic():
            order = Order.objects.create(student=student, course=course, amount=course.price)
            gateway = get_gateway()
            gw_result = gateway.create_order(
                amount_rupees=course.price,
                receipt=order.order_id,
                notes={"student_id": student.student_id, "course_id": course.id},
            )
            order.gateway_order_id = gw_result["gateway_order_id"]
            order.save(update_fields=["gateway_order_id"])

        return Response(
            {
                "order": OrderSerializer(order).data,
                "checkout_config": gw_result["checkout_config"],
            },
            status=status.HTTP_201_CREATED,
        )


class ConfirmPaymentView(generics.GenericAPIView):
    """Optional fast-path called by the frontend right after the checkout
    widget reports success. Only flips UI state / creates a `pending`
    Payment row for display - actual paid/enrolled state is set by the
    webhook below, which is the only path that trusts the gateway."""
    permission_classes = [IsAuthenticated]
    serializer_class = ConfirmPaymentSerializer
    throttle_scope = "payments"

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            order = Order.objects.get(order_id=data["order_id"], student=request.user.student_profile)
        except Order.DoesNotExist:
            raise ValidationError({"order_id": "Order not found."})

        gateway_payment_id = (
            data.get("razorpay_payment_id") or data.get("mock_payment_id") or data.get("gateway_payment_id") or ""
        )
        Payment.objects.get_or_create(
            order=order,
            defaults={
                "payment_id": gateway_payment_id or f"pending_{order.order_id}",
                "method": data["method"],
                "status": Payment.Status.PENDING,
                "amount": order.amount,
            },
        )
        return Response({"detail": "Received. Awaiting gateway confirmation via webhook."})


def _apply_gateway_event(payload: dict):
    """Single source of truth for turning a verified gateway event into
    Order/Payment/Enrollment writes. Used by both the real webhook endpoint
    and the mock-mode simulate endpoint, so there is exactly one code path
    that can ever mark an order paid."""
    gateway_order_id = payload.get("order_id") or payload.get("payload", {}).get("order", {}).get(
        "entity", {}
    ).get("id")
    gateway_payment_id = payload.get("payment_id") or payload.get("payload", {}).get("payment", {}).get(
        "entity", {}
    ).get("id", f"pay_{gateway_order_id}")
    event_status = payload.get("status", "success")

    order = Order.objects.select_related("student", "course").get(gateway_order_id=gateway_order_id)

    with transaction.atomic():
        payment, _ = Payment.objects.get_or_create(
            order=order,
            defaults={"payment_id": gateway_payment_id, "amount": order.amount},
        )
        if event_status == "success":
            payment.status = Payment.Status.SUCCESS
            payment.payment_id = gateway_payment_id
            payment.gateway_response = payload
            payment.verified_at = timezone.now()
            payment.save()

            order.status = Order.Status.PAID
            order.save(update_fields=["status"])

            Enrollment.objects.get_or_create(
                student=order.student, course=order.course, defaults={"order": order}
            )
        else:
            payment.status = Payment.Status.FAILED
            payment.gateway_response = payload
            payment.save()
            order.status = Order.Status.FAILED
            order.save(update_fields=["status"])
    return order


class PaymentWebhookView(APIView):
    """Server-to-server callback from the payment gateway. Signature
    verification is mandatory - this is the ONLY place (along with the
    mock-mode simulate endpoint below) an order is marked paid and an
    Enrollment is created."""
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        gateway = get_gateway()
        signature = request.headers.get("X-Webhook-Signature", "") or request.headers.get(
            "X-Razorpay-Signature", ""
        )
        if not gateway.verify_webhook_signature(payload_body=request.body, signature=signature):
            logger.warning("Rejected webhook: bad signature")
            return Response({"detail": "Invalid signature."}, status=status.HTTP_400_BAD_REQUEST)

        payload = json.loads(request.body or "{}")
        try:
            _apply_gateway_event(payload)
        except Order.DoesNotExist:
            logger.warning("Webhook for unknown order")
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response({"detail": "ok"})


class SimulateMockPaymentView(generics.GenericAPIView):
    """
    DEV/DEMO ONLY. Lets the frontend walk through a full, realistic
    Student -> Course -> Checkout -> Payment -> Enrollment cycle without a
    real payment gateway account, by generating the same signed event a
    real gateway webhook would send and running it through the identical
    verification + write path as PaymentWebhookView. Refuses to run unless
    PAYMENT_GATEWAY=mock, so it can never be used to bypass a real gateway.
    """
    permission_classes = [IsAuthenticated]
    throttle_scope = "payments"

    def post(self, request):
        from django.conf import settings

        if settings.PAYMENT_GATEWAY != "mock":
            raise PermissionDenied("Simulated payments are only available in mock mode.")
        if not hasattr(request.user, "student_profile"):
            raise PermissionDenied("Only students can complete a course purchase.")

        order_id = request.data.get("order_id")
        try:
            order = Order.objects.get(order_id=order_id, student=request.user.student_profile)
        except Order.DoesNotExist:
            raise ValidationError({"order_id": "Order not found."})

        payload = {
            "order_id": order.gateway_order_id,
            "payment_id": f"mock_pay_{order.order_id}",
            "status": "success",
            "method": request.data.get("method", "upi"),
        }
        _apply_gateway_event(payload)
        order.refresh_from_db()
        return Response({"detail": "Payment simulated successfully.", "order": OrderSerializer(order).data})


class OrderViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = OrderSerializer
    filterset_fields = ["student", "course", "status"]

    def get_queryset(self):
        user = self.request.user
        qs = Order.objects.select_related("student__user", "course")
        if user_is_admin(user):
            return qs
        if hasattr(user, "student_profile"):
            return qs.filter(student=user.student_profile)
        if user.role == Role.PARENT:
            parent = parent_profile_of(user)
            return qs.filter(student__parents=parent) if parent else qs.none()
        return qs.none()


class EnrollmentViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = EnrollmentSerializer
    filterset_fields = ["student", "course"]

    def get_queryset(self):
        user = self.request.user
        qs = Enrollment.objects.select_related("student__user", "course")
        if user_is_admin(user):
            return qs
        if hasattr(user, "student_profile"):
            return qs.filter(student=user.student_profile)
        if user.role == Role.PARENT:
            parent = parent_profile_of(user)
            return qs.filter(student__parents=parent) if parent else qs.none()
        return qs.none()
