from rest_framework import serializers
from .models import StudentMLDataset


class StudentMLDatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentMLDataset
        fields = "__all__"
        read_only_fields = ("snapshot_date",)
