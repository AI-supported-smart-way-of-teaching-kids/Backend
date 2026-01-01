from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StudentMLDatasetViewSet

router = DefaultRouter()
router.register(r"datasets", StudentMLDatasetViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
