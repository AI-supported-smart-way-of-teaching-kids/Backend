from rest_framework import serializers
from .models import StudentRealtimeAggregate
from profiles.models import ChildProfile

class StudentRealtimeAggregateSerializer(serializers.ModelSerializer):
    child = serializers.PrimaryKeyRelatedField( \
        queryset=ChildProfile.objects.all(), allow_null=True)

    class Meta:
        model = StudentRealtimeAggregate
        fields = '__all__'
        read_only_fields = ('updated_at',)
