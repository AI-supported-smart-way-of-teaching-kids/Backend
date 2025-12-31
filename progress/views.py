from django_filters.rest_framework import DjangoFilterBackend

# ----------------------
# Custom Permission
# ----------------------
from rest_framework import permissions
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import Badge, ChildBadge, Progress
from .serializers import BadgeSerializer, ChildBadgeSerializer, ProgressSerializer


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Allows full access to admin users; read-only for others.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


# ----------------------
# Read-Only ViewSets
# ----------------------


class ProgressViewSet(ReadOnlyModelViewSet):
    serializer_class = ProgressSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["child__user__username", "child__full_name"]  # example
    ordering_fields = ["score", "date"]  # example

    def get_queryset(self):
        user = self.request.user
        if getattr(user, "is_admin", False) or getattr(user, "is_staff", False):
            return Progress.objects.all()
        if getattr(user, "is_parent", False):
            from profiles.models import ChildProfile

            children = ChildProfile.objects.filter(parent=user)
            return Progress.objects.filter(child__in=children)
        return Progress.objects.none()

    def get_serializer_context(self):
        return {"request": self.request}


class BadgeViewSet(ReadOnlyModelViewSet):
    queryset = Badge.objects.all()
    serializer_class = BadgeSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["created_at", "level"]

    def get_serializer_context(self):
        return {"request": self.request}


class ChildBadgeViewSet(ReadOnlyModelViewSet):
    serializer_class = ChildBadgeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["child__user__username", "badge__name"]
    ordering_fields = ["awarded_at"]

    def get_queryset(self):
        user = self.request.user
        if getattr(user, "is_admin", False) or getattr(user, "is_staff", False):
            return ChildBadge.objects.all()
        if getattr(user, "is_parent", False):
            from profiles.models import ChildProfile

            children = ChildProfile.objects.filter(parent=user)
            return ChildBadge.objects.filter(child__in=children)
        return ChildBadge.objects.none()

    def get_serializer_context(self):
        return {"request": self.request}
