from rest_framework import serializers

from .models import (
    LessonInteractionsRaw,
    MLModel,
    MLStudentMap,
    ProgressRaw,
    QuizAttemptsRaw,
    Recommendation,
)


class MLModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = MLModel
        fields = ["id", "name", "version", "file_path", "metadata", "created_at"]
        read_only_fields = ["id", "created_at"]


class MLStudentMapSerializer(serializers.ModelSerializer):
    child_nickname = serializers.CharField(source="child.nickname", read_only=True)

    class Meta:
        model = MLStudentMap
        fields = [
            "ml_student_id",
            "student_uuid",
            "child",
            "child_nickname",
            "mapped_at",
        ]
        read_only_fields = ["mapped_at"]


class RecommendationSerializer(serializers.ModelSerializer):
    child_nickname = serializers.CharField(source="child.nickname", read_only=True)
    lesson_title = serializers.CharField(source="lesson.title", read_only=True)
    lesson_slug = serializers.CharField(source="lesson.slug", read_only=True)
    lesson_thumbnail = serializers.URLField(
        source="lesson.thumbnail_url", read_only=True
    )
    model_name = serializers.CharField(source="model.name", read_only=True)

    class Meta:
        model = Recommendation
        fields = [
            "id",
            "child",
            "child_nickname",
            "lesson",
            "lesson_title",
            "lesson_slug",
            "lesson_thumbnail",
            "confidence_score",
            "reason",
            "model",
            "model_name",
            "generated_at",
        ]
        read_only_fields = ["id", "generated_at"]


class LessonInteractionsRawSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonInteractionsRaw
        fields = [
            "ml_student_id",
            "student_uuid",
            "lesson_id",
            "time_spent",
            "video_watch_percentage",
            "number_of_clicks",
            "completion_status",
        ]

    def create(self, validated_data):
        # resolve child or raise
        student_uuid = validated_data.get("student_uuid")
        ml_student_id = validated_data.get("ml_student_id")
        child = None
        if student_uuid:
            try:
                from profiles.models import ChildProfile

                child = ChildProfile.objects.get(uuid=student_uuid)
            except ChildProfile.DoesNotExist:
                pass
        if not child and ml_student_id:
            try:
                from .models import MLStudentMap

                child = MLStudentMap.objects.get(ml_student_id=ml_student_id).child
            except MLStudentMap.DoesNotExist:
                pass
        if not child:
            raise serializers.ValidationError("Child not found for ML mapping.")
        validated_data["child"] = child
        return super().create(validated_data)


class QuizAttemptsRawSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAttemptsRaw
        fields = [
            "ml_student_id",
            "student_uuid",
            "lesson_id",
            "attempt_number",
            "score",
            "wrong_questions",
            "response_time",
        ]

    def create(self, validated_data):
        # same resolution logic as above
        student_uuid = validated_data.get("student_uuid")
        ml_student_id = validated_data.get("ml_student_id")
        child = None
        if student_uuid:
            try:
                from profiles.models import ChildProfile

                child = ChildProfile.objects.get(uuid=student_uuid)
            except ChildProfile.DoesNotExist:
                pass
        if not child and ml_student_id:
            try:
                from .models import MLStudentMap

                child = MLStudentMap.objects.get(ml_student_id=ml_student_id).child
            except MLStudentMap.DoesNotExist:
                pass
        if not child:
            raise serializers.ValidationError("Child not found for ML mapping.")
        validated_data["child"] = child
        return super().create(validated_data)


class ProgressRawSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgressRaw
        fields = [
            "ml_student_id",
            "student_uuid",
            "lessons_completed",
            "badges_earned",
            "streak_days",
            "topic_mastery",
        ]

    def create(self, validated_data):
        # same child resolution
        student_uuid = validated_data.get("student_uuid")
        ml_student_id = validated_data.get("ml_student_id")
        child = None
        if student_uuid:
            try:
                from profiles.models import ChildProfile

                child = ChildProfile.objects.get(uuid=student_uuid)
            except ChildProfile.DoesNotExist:
                pass
        if not child and ml_student_id:
            try:
                from .models import MLStudentMap

                child = MLStudentMap.objects.get(ml_student_id=ml_student_id).child
            except MLStudentMap.DoesNotExist:
                pass
        if not child:
            raise serializers.ValidationError("Child not found for ML mapping.")
        validated_data["child"] = child
        return super().create(validated_data)
