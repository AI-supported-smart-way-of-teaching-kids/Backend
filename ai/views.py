from django.db.models import Prefetch
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import MLModel, MLStudentMap, Recommendation
from .serializers import (
    LessonInteractionsRawSerializer,
    MLModelSerializer,
    MLStudentMapSerializer,
    ProgressRawSerializer,
    QuizAttemptsRawSerializer,
    RecommendationSerializer,
)


# ----------------------
# ML Model Management
# ----------------------
class MLModelViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for ML models.
    """

    queryset = MLModel.objects.all()
    serializer_class = MLModelSerializer
    permission_classes = [permissions.IsAuthenticated]


# ----------------------
# Recommendation Serving
# ----------------------
class RecommendationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only access to recommendations for students.
    Ordered by confidence_score descending.
    """

    serializer_class = RecommendationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Recommendation.objects.all().order_by("-confidence_score")

        # If the user is a child, filter recommendations dedicated to them
        if hasattr(user, "childprofile"):  # assuming a ChildProfile relation
            queryset = queryset.filter(student=user.childprofile)
        return queryset.prefetch_related(
            Prefetch("lesson")  # optional: prefetch related lesson/video
        )


# ----------------------
# ML Data Ingestion
# ----------------------
class MLDataIngestionView(APIView):
    """
    Endpoint for ingesting raw ML data from the frontend or external sources.
    Example data_types: lesson_interactions, quiz_attempts, progress
    """

    permission_classes = [permissions.AllowAny]  # secure in production

    def post(self, request, data_type):
        data = request.data
        many = isinstance(data, list)

        if data_type == "lesson_interactions":
            serializer = LessonInteractionsRawSerializer(data=data, many=many)
        elif data_type == "quiz_attempts":
            serializer = QuizAttemptsRawSerializer(data=data, many=many)
        elif data_type == "progress":
            serializer = ProgressRawSerializer(data=data, many=many)
        else:
            return Response(
                {"error": "invalid data_type"}, status=status.HTTP_400_BAD_REQUEST
            )

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "ingested", "count": len(serializer.validated_data)},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ----------------------
# Student-ML Mapping
# ----------------------
class MLStudentMapViewSet(viewsets.ModelViewSet):
    """
    Map backend students to ML identifiers or feature vectors.
    """

    queryset = MLStudentMap.objects.all()
    serializer_class = MLStudentMapSerializer
    permission_classes = [permissions.IsAuthenticated]
