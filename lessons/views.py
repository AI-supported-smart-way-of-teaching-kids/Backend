# lessons/views.py
import logging

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
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


# -----------------------------------------------------------------------------
# Custom permission
# -----------------------------------------------------------------------------
class IsTeacherOrAdmin(IsAuthenticated):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (getattr(user, "is_admin", False) or getattr(user, "is_teacher", False))
        )


# -----------------------------------------------------------------------------
# Collection
# -----------------------------------------------------------------------------
class CollectionViewSet(ModelViewSet):
    queryset = Collection.objects.all().order_by("-created_at")
    serializer_class = CollectionSerializer
    permission_classes = [AllowAny]

    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["title", "description"]
    ordering_fields = ["title", "created_at"]


# -----------------------------------------------------------------------------
# Lesson
# -----------------------------------------------------------------------------
class LessonViewSet(ModelViewSet):
    queryset = Lesson.objects.all().order_by("-created_at")

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["difficulty", "teacher", "collection", "is_published"]
    search_fields = ["title", "description", "tags"]
    ordering_fields = ["created_at", "title"]

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsTeacherOrAdmin()]
        return [AllowAny()]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return LessonCreateSerializer
        return LessonSerializer

    def get_serializer_context(self):
        return {"request": self.request}

    # -------------------------------------------------------------------------
    # Track lesson progress (Swagger-friendly)
    # -------------------------------------------------------------------------
    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path="track-progress",
    )
    def track_progress(self, request, pk=None):
        """
        POST body:
        {
          "child_id": 1,
          "completion_status": true,
          "time_spent": 120,
          "video_watch_percentage": 80,
          "number_of_clicks": 5
        }
        """
        from profiles.models import ChildProfile
        from progress.models import Progress

        lesson = self.get_object()
        child_id = request.data.get("child_id")

        if not child_id:
            return Response(
                {"detail": "child_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        child = get_object_or_404(ChildProfile, id=child_id)

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

        # -------------------- Optional ML raw event --------------------
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
        except Exception as e:
            logger.warning("ML event skipped: %s", e)

        return Response({"detail": "Progress tracked"}, status=status.HTTP_200_OK)


# -----------------------------------------------------------------------------
# Media upload
# -----------------------------------------------------------------------------
class MediaUploadViewSet(ModelViewSet):
    queryset = MediaUpload.objects.all().order_by("-created_at")
    serializer_class = MediaUploadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if getattr(user, "is_admin", False):
            return MediaUpload.objects.all()
        return MediaUpload.objects.filter(uploader=user)

    def get_serializer_context(self):
        return {"request": self.request}

    def perform_create(self, serializer):
        user = self.request.user
        lesson = serializer.validated_data.get("lesson")

        if not getattr(user, "is_admin", False):
            if not lesson.teacher or lesson.teacher.user != user:
                return Response(
                    {"detail": "You can upload media only to your own lessons"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        serializer.save(uploader=user)
