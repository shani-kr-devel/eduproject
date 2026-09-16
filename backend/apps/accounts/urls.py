from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

router = DefaultRouter()
router.register("admin/users", views.AdminUserViewSet, basename="admin-users")
router.register("students", views.StudentProfileViewSet, basename="students")
router.register("teachers", views.TeacherProfileViewSet, basename="teachers")
router.register("parents", views.ParentProfileViewSet, basename="parents")

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", views.MeView.as_view(), name="me"),
    path("parent/search-child/", views.SearchChildView.as_view(), name="search-child"),
    path("parent/link-child/", views.LinkChildView.as_view(), name="link-child"),
    path("", include(router.urls)),
]
