import logging
from django.contrib.auth import authenticate
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import AuditLog
from .models import ChildProfile, TeacherProfile, User
from .serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    LoginSerializer,
    ChildProfileCreateSerializer,
    ChildProfileParentSerializer,
    ChildProfilePublicSerializer,
    TeacherProfileSerializer,
)

logger = logging.getLogger(__name__)


# -----------------------
# User Views
# -----------------------
class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.ADMIN:
            return User.objects.all().order_by("-date_joined")
        return User.objects.filter(id=user.id)

    @action(detail=False, methods=["get", "put"])
    def profile(self, request):
        # GET → read-only (FIXED)
        if request.method == "GET":
            serializer = self.get_serializer(request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # PUT → update
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class RegisterView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        self.user = serializer.save()
        AuditLog.objects.create(
            user=self.user,
            action="USER_REGISTERED",
            resource_id=str(self.user.id),
            meta={"email": self.user.email},
        )

    def create(self, request, *args, **kwargs):
        super().create(request, *args, **kwargs)
        refresh = RefreshToken.for_user(self.user)
        return Response(
            {
                "user": UserSerializer(self.user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            request,
            username=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )

        if not user:
            AuditLog.objects.create(action="LOGIN_FAILED")
            return Response(
                {"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)
        AuditLog.objects.create(
            user=user, action="LOGIN_SUCCESS", resource_id=str(user.id)
        )

        return Response(
            {
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }
        )


# -----------------------
# Child Profile ViewSet
# -----------------------
class ChildProfileViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.ADMIN:
            return ChildProfile.objects.all()
        if user.role == User.Role.PARENT:
            return ChildProfile.objects.filter(parent=user)
        if user.role == User.Role.TEACHER:
            return ChildProfile.objects.all()
        return ChildProfile.objects.none()

    def get_serializer_class(self):
        user = self.request.user
        if self.action in ("create", "update", "partial_update"):
            return ChildProfileCreateSerializer
        if user.role in (User.Role.PARENT, User.Role.ADMIN):
            return ChildProfileParentSerializer
        return ChildProfilePublicSerializer

    def perform_create(self, serializer):
        if self.request.user.role != User.Role.PARENT:
            raise PermissionDenied("Only parents can create child profiles.")
        serializer.save(parent=self.request.user)

    def perform_update(self, serializer):
        if self.request.user.role != User.Role.PARENT:
            raise PermissionDenied("Only parents can update child profiles.")
        serializer.save()

    def perform_destroy(self, instance):
        if self.request.user.role != User.Role.PARENT:
            raise PermissionDenied("Only parents can delete child profiles.")
        instance.delete()

    @action(detail=True, methods=["get"])
    def progress(self, request, pk=None):
        # FETCH CHILD WITHOUT ROLE FILTER (FIXED)
        child = ChildProfile.objects.filter(uuid=pk).first()
        if not child:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # PERMISSION CHECK AFTER EXISTENCE
        if request.user.role == User.Role.PARENT and child.parent != request.user:
            raise PermissionDenied("Access denied.")

        from progress.models import Progress
        from progress.serializers import ProgressSerializer

        qs = Progress.objects.filter(child=child)
        return Response(
            ProgressSerializer(qs, many=True).data, status=status.HTTP_200_OK
        )


# -----------------------
# Teacher Profile ViewSet (read-only)
# -----------------------
class TeacherProfileViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TeacherProfile.objects.all().order_by("-created_at")
    serializer_class = TeacherProfileSerializer
    permission_classes = [IsAuthenticated]
