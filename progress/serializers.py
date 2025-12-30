from rest_framework import serializers

from .models import Badge, ChildBadge, Progress


class ProgressSerializer(serializers.ModelSerializer):
    child_nickname = serializers.CharField(source="child.nickname", read_only=True)
    lesson_title = serializers.CharField(source="lesson.title", read_only=True)
    lesson_slug = serializers.CharField(source="lesson.slug", read_only=True)

    class Meta:
        model = Progress
        fields = [
            "id",
            "child",
            "child_nickname",
            "lesson",
            "lesson_title",
            "lesson_slug",
            "status",
            "points_earned",
            "last_accessed",
            "completion_date",
        ]
        read_only_fields = ["id", "completion_date"]


class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = ["id", "name", "description", "created_at"]
        read_only_fields = ["id", "created_at"]


class ChildBadgeSerializer(serializers.ModelSerializer):
    badge_name = serializers.CharField(source="badge.name", read_only=True)
    child_nickname = serializers.CharField(source="child.nickname", read_only=True)

    class Meta:
        model = ChildBadge
        fields = ["id", "child", "child_nickname", "badge", "badge_name", "awarded_at"]
        read_only_fields = ["id", "awarded_at"]
