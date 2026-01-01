from rest_framework import serializers
from .models import MLModel, MLStudentMap, Recommendation
from profiles.models import ChildProfile
from lessons.models import Lesson

class MLModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = MLModel
        fields = '__all__'
        read_only_fields = ('created_at',)

class MLStudentMapSerializer(serializers.ModelSerializer):
    child = serializers.PrimaryKeyRelatedField(queryset=ChildProfile.objects.all(), allow_null=True)
    class Meta:
        model = MLStudentMap
        fields = '__all__'
        read_only_fields = ('mapped_at',)

class RecommendationSerializer(serializers.ModelSerializer):
    child = serializers.PrimaryKeyRelatedField(queryset=ChildProfile.objects.all())
    lesson = serializers.PrimaryKeyRelatedField(queryset=Lesson.objects.all())
    model = MLModelSerializer(read_only=True)
    
    class Meta:
        model = Recommendation
        fields = '__all__'
        read_only_fields = ('generated_at',)
