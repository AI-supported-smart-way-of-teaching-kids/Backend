from rest_framework import serializers
from .models import Collection, Lesson, MediaUpload


# ------------------------------
# Collection Serializer
# ------------------------------
class CollectionSerializer(serializers.ModelSerializer):
    lesson_count = serializers.IntegerField(source="lessons.count", read_only=True)

    class Meta:
        model = Collection
        fields = ["id", "title", "slug", "description", "lesson_count", "created_at"]
        read_only_fields = ["id", "slug", "created_at"]


# ------------------------------
# MediaUpload Serializer
# ------------------------------
class MediaUploadSerializer(serializers.ModelSerializer):
    uploader_username = serializers.CharField(
        source="uploader.username", read_only=True
    )

    class Meta:
        model = MediaUpload
        fields = [
            "id",
            "lesson",
            "file",
            "file_url",
            "file_type",
            "status",
            "uploader",
            "uploader_username",
            "created_at",
        ]
        read_only_fields = ["id", "status", "uploader", "created_at"]

    def validate(self, attrs):
        """
        Custom validation to provide helpful error messages.
        """
        # Check if file is provided when creating
        if not self.instance:  # Creating new upload
            if "file" not in attrs and "file_url" not in attrs:
                raise serializers.ValidationError(
                    {"file": "Either 'file' or 'file_url' must be provided."}
                )

        # Validate file_type is in allowed choices
        file_type = attrs.get("file_type")
        if file_type:
            valid_types = [choice[0] for choice in MediaUpload.FileType.choices]
            if file_type not in valid_types:
                raise serializers.ValidationError(
                    {
                        "file_type": f"Invalid file type. Must be one of: {', '.join(valid_types)}"
                    }
                )

        return attrs


# ------------------------------
# Lesson Serializer (for listing)
# ------------------------------
class LessonSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source="teacher.user.username", read_only=True)
    collection_title = serializers.CharField(source="collection.title", read_only=True)
    media_uploads = MediaUploadSerializer(many=True, read_only=True)

    class Meta:
        model = Lesson
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "video",
            "video_url",
            "thumbnail",
            "duration_seconds",
            "difficulty",
            "teacher",
            "teacher_name",
            "collection",
            "collection_title",
            "tags",
            "is_published",
            "media_uploads",
            "created_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "teacher_name", "media_uploads"]


# ------------------------------
# Lesson Create Serializer (for creating lessons)
# ------------------------------
class LessonCreateSerializer(serializers.ModelSerializer):
    # Fix for 'tags': accept list input from JSON
    tags = serializers.ListField(child=serializers.CharField(), required=False)

    class Meta:
        model = Lesson
        fields = [
            "title",
            "description",
            "video",
            "video_url",
            "thumbnail",
            "duration_seconds",
            "difficulty",
            "collection",
            "tags",
            "is_published",
        ]

    def validate(self, attrs):
        # Allow either video (file) OR video_url (link)
        if not attrs.get("video") and not attrs.get("video_url"):
            raise serializers.ValidationError(
                "Either a video file ('video') or a video URL ('video_url') is required."
            )
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        if not request:
            raise serializers.ValidationError("Request is required in context.")

        user = request.user
        teacher_profile = getattr(user, "teacher_profile", None)  # correct FK attribute
        if not teacher_profile:
            raise serializers.ValidationError("Only teachers can create lessons.")

        # Attach teacher automatically
        validated_data["teacher"] = teacher_profile
        return super().create(validated_data)
