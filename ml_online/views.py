from rest_framework import viewsets, permissions
from .models import StudentRealtimeAggregate
from .serializers import StudentRealtimeAggregateSerializer


class StudentRealtimeAggregateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StudentRealtimeAggregate.objects.all().select_related("child")
    serializer_class = StudentRealtimeAggregateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["ml_student_id", "child"]
    search_fields = ["ml_student_id"]
