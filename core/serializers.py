from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "user",
            "user_name",
            "action",
            "resource_id",
            "meta",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_user_name(self, obj):
        return obj.user.username if obj.user else None
