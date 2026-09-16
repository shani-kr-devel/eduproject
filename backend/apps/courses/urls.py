from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("courses", views.CourseViewSet, basename="courses")
router.register("course-content", views.CourseContentViewSet, basename="course-content")
router.register("quiz-questions", views.CourseQuizQuestionViewSet, basename="quiz-questions")
router.register("quiz-attempts", views.CourseQuizAttemptViewSet, basename="quiz-attempts")
router.register("assignments", views.CourseAssignmentViewSet, basename="course-assignments")
router.register("orders", views.OrderViewSet, basename="orders")
router.register("enrollments", views.EnrollmentViewSet, basename="enrollments")

urlpatterns = [
    path("checkout/", views.CheckoutView.as_view(), name="checkout"),
    path("confirm-payment/", views.ConfirmPaymentView.as_view(), name="confirm-payment"),
    path("mock/simulate-payment/", views.SimulateMockPaymentView.as_view(), name="simulate-mock-payment"),
    path("webhook/", views.PaymentWebhookView.as_view(), name="payment-webhook"),
    path("", include(router.urls)),
]
