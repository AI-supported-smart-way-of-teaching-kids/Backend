# ai/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    MLDataIngestionView,
    MLModelViewSet,
    MLStudentMapViewSet,
    RecommendationViewSet,
)

router = DefaultRouter()
router.register(r"recommendations", RecommendationViewSet, basename="recommendation")
router.register(r"ml-student-maps", MLStudentMapViewSet, basename="ml-student-map")
router.register(r"ml-models", MLModelViewSet, basename="ml-model")

urlpatterns = [
    # ML ingestion endpoint (POST JSON list or single)
    path("ml/ingest/<str:data_type>/", MLDataIngestionView.as_view(), name="ml-ingest"),
    # Router
    path("", include(router.urls)),
]
