from rest_framework import viewsets, permissions
from .models import StudentMLDataset
from .serializers import StudentMLDatasetSerializer

class StudentMLDatasetViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StudentMLDataset.objects.all()
    serializer_class = StudentMLDatasetSerializer
    permission_classes = [permissions.IsAdminUser]

