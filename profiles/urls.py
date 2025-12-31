# profiles/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    ChildProfileViewSet,
    LoginView,
    RegisterView,
    TeacherProfileViewSet,
    UserViewSet,
)

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"children", ChildProfileViewSet, basename="child")
router.register(r"teachers", TeacherProfileViewSet, basename="teacher")

urlpatterns = [
    # Auth
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # API router
    path("", include(router.urls)),
]
