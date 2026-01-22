import logging

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Collection, Lesson, MediaUpload
from .serializers import (
    CollectionSerializer,
    LessonCreateSerializer,
    LessonSerializer,
    MediaUploadSerializer,
)

logger = logging.getLogger(__name__)

# =============================================================================
# PERMISSIONS
# =============================================================================


class IsTeacherOrAdmin(IsAuthenticated):
    """
    Allows access only to authenticated users who are teachers or admins.
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        return getattr(user, "is_admin", False) or getattr(user, "is_teacher", False)


# =============================================================================
# COLLECTION VIEWSET
# =============================================================================


class CollectionViewSet(ModelViewSet):
    """
    Manage lesson collections.
    """

    queryset = Collection.objects.prefetch_related("lessons").order_by("-created_at")
    serializer_class = CollectionSerializer
    permission_classes = [AllowAny]

    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ("title", "description")
    ordering_fields = ("title", "created_at")


# =============================================================================
# LESSON VIEWSET
# =============================================================================


class LessonViewSet(ModelViewSet):
    """
    Manage lessons and track student progress.
    """

    parser_classes = [
        MultiPartParser,
        FormParser,
    ]  # Add parser support for file uploads

    @extend_schema(
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "video": {"type": "string", "format": "binary"},
                    "video_url": {"type": "string"},
                    "thumbnail": {"type": "string", "format": "binary"},
                    "duration_seconds": {"type": "integer"},
                    "difficulty": {
                        "type": "string",
                        "enum": [c[0] for c in Lesson.Difficulty.choices],
                    },
                    "collection": {"type": "integer"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "is_published": {"type": "boolean"},
                },
                "required": ["title", "description"],
            }
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "video": {"type": "string", "format": "binary"},
                    "video_url": {"type": "string"},
                    "thumbnail": {"type": "string", "format": "binary"},
                    "duration_seconds": {"type": "integer"},
                    "difficulty": {
                        "type": "string",
                        "enum": [c[0] for c in Lesson.Difficulty.choices],
                    },
                    "collection": {"type": "integer"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "is_published": {"type": "boolean"},
                },
            }
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "video": {"type": "string", "format": "binary"},
                    "video_url": {"type": "string"},
                    "thumbnail": {"type": "string", "format": "binary"},
                    "duration_seconds": {"type": "integer"},
                    "difficulty": {
                        "type": "string",
                        "enum": [c[0] for c in Lesson.Difficulty.choices],
                    },
                    "collection": {"type": "integer"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "is_published": {"type": "boolean"},
                },
            }
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    queryset = (
        Lesson.objects.select_related("teacher", "teacher__user", "collection")
        .prefetch_related("media_uploads")
        .order_by("-created_at")
    )

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ("difficulty", "teacher", "collection", "is_published")
    search_fields = ("title", "description", "tags")
    ordering_fields = ("created_at", "title")

    # -------------------- Permissions & Serializers --------------------

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [IsTeacherOrAdmin()]
        return [AllowAny()]

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return LessonCreateSerializer
        return LessonSerializer

    def get_serializer_context(self):
        return {"request": self.request}

    # -------------------- Custom Actions --------------------

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path="track-progress",
    )
    def track_progress(self, request, pk=None):
        """
        Track child progress for a lesson.
        """
        from profiles.models import ChildProfile

        lesson = self.get_object()
        child_id = request.data.get("child_id")

        if not child_id:
            return Response(
                {"detail": "child_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        child = get_object_or_404(ChildProfile, id=child_id)

        self._update_progress(request, child, lesson)
        self._log_ml_interaction(request, child, lesson)

        return Response(
            {"detail": "Progress tracked"},
            status=status.HTTP_200_OK,
        )

    # -------------------- Helpers --------------------

    def _update_progress(self, request, child, lesson):
        """
        Create or update Progress record.
        """
        from progress.models import Progress

        progress, _ = Progress.objects.get_or_create(
            child=child,
            lesson=lesson,
            defaults={"status": Progress.Status.IN_PROGRESS},
        )

        if request.data.get("completion_status"):
            progress.status = Progress.Status.COMPLETED
            progress.completion_date = timezone.now()

        progress.last_accessed = timezone.now()
        progress.save()
        return progress

    def _log_ml_interaction(self, request, child, lesson):
        """
        Log ML-related lesson interaction data.
        """
        try:
            from ai.models import LessonInteractionsRaw, MLStudentMap

            ml_map = MLStudentMap.objects.filter(child=child).first()

            LessonInteractionsRaw.objects.create(
                ml_student_id=getattr(ml_map, "ml_student_id", 0),
                student_uuid=str(child.uuid),
                child=child,
                lesson_id=lesson.id,
                time_spent=float(request.data.get("time_spent", 0)),
                video_watch_percentage=float(
                    request.data.get("video_watch_percentage", 0)
                ),
                number_of_clicks=int(request.data.get("number_of_clicks", 0)),
                completion_status=bool(request.data.get("completion_status", False)),
            )
        except Exception as exc:
            logger.warning("ML event skipped: %s", exc)


# =============================================================================
# MEDIA UPLOAD VIEWSET
# =============================================================================


class MediaUploadViewSet(ModelViewSet):
    """
    Handle lesson-related media uploads.
    """

    serializer_class = MediaUploadSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "lesson": {"type": "integer"},
                    "file": {"type": "string", "format": "binary"},
                    "file_url": {"type": "string"},
                    "file_type": {
                        "type": "string",
                        "enum": [c[0] for c in MediaUpload.FileType.choices],
                    },
                },
                "required": ["lesson", "file_type"],
            }
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        queryset = MediaUpload.objects.select_related("lesson", "uploader")

        if getattr(user, "is_admin", False):
            return queryset.order_by("-created_at")

        return queryset.filter(uploader=user).order_by("-created_at")

    def get_serializer_context(self):
        return {"request": self.request}

    def perform_create(self, serializer):
        user = self.request.user

        # Validate lesson exists
        lesson = serializer.validated_data.get("lesson")
        if not lesson:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"lesson": "Lesson is required."})

        # Validate file is present
        if (
            "file" not in self.request.FILES
            and "file_url" not in serializer.validated_data
        ):
            from rest_framework.exceptions import ValidationError

            raise ValidationError(
                {
                    "file": "No file was uploaded. \
                    Ensure the request uses multipart/form-data encoding."
                }
            )

        # Check ownership (unless admin)
        if not getattr(user, "is_admin", False):
            self._validate_lesson_ownership(user, lesson)

        try:
            serializer.save(uploader=user)
            logger.info(
                f"Media upload created for lesson {lesson.id} by user {user.username}"
            )
        except Exception as exc:
            logger.error(f"Media upload failed for lesson {lesson.id}: {exc}")
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"detail": f"Upload failed: {str(exc)}"})

    def _validate_lesson_ownership(self, user, lesson):
        """
        Ensure only lesson owners can upload media.
        """
        if lesson.teacher.user != user:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("You do not own this lesson.")
