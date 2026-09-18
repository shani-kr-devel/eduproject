from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("homework", views.HomeworkViewSet, basename="homework")
router.register("tests", views.TestViewSet, basename="tests")
router.register("test-questions", views.TestQuestionViewSet, basename="test-questions")
router.register("student-groups", views.StudentGroupViewSet, basename="student-groups")
router.register("test-attempts", views.TestAttemptViewSet, basename="test-attempts")
router.register("feedback", views.FeedbackViewSet, basename="feedback")

urlpatterns = [
    path("performance/<int:student_pk>/", views.PerformanceReportView.as_view(), name="performance-report"),
    path("", include(router.urls)),
]
