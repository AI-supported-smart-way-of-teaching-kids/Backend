from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MLModelViewSet, MLStudentMapViewSet, RecommendationViewSet

router = DefaultRouter()
router.register(r"models", MLModelViewSet)
router.register(r"student-maps", MLStudentMapViewSet)
router.register(r"recommendations", RecommendationViewSet)

urlpatterns = [
    path("ml/", include(router.urls)),
]
