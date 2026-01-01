from rest_framework import viewsets, permissions
from .models import MLModel, MLStudentMap, Recommendation
from .serializers import (
    MLModelSerializer,
    MLStudentMapSerializer,
    RecommendationSerializer,
)


class MLModelViewSet(viewsets.ModelViewSet):
    queryset = MLModel.objects.all().order_by("-created_at")
    serializer_class = MLModelSerializer
    permission_classes = [permissions.IsAdminUser]


class MLStudentMapViewSet(viewsets.ModelViewSet):
    queryset = MLStudentMap.objects.all()
    serializer_class = MLStudentMapSerializer
    permission_classes = [permissions.IsAdminUser]


class RecommendationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Recommendation.objects.all().select_related("child", "lesson", "model")
    serializer_class = RecommendationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["child", "model"]
    search_fields = ["child__user__username", "lesson__title"]
