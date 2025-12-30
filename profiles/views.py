# profiles/views.py
import logging

from django.contrib.auth import authenticate
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import AuditLog

from .models import ChildProfile, TeacherProfile, User
from .serializers import (
    ChildProfileCreateSerializer,
    ChildProfileSerializer,
    LoginSerializer,
    TeacherProfileSerializer,
    UserRegistrationSerializer,
    UserSerializer,
)

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# User viewset
# -----------------------------------------------------------------------------
class UserViewSet(ModelViewSet):
    """
    Manage users. Admins can list all users; regular users can view/update only themselves.
    """

    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if getattr(user, "is_admin", False):
            return User.objects.all().order_by("-date_joined")
        return User.objects.filter(id=user.id)

    @action(detail=False, methods=["get", "put"], permission_classes=[IsAuthenticated])
    def profile(self, request):
        """Retrieve or update current user's profile."""
        if request.method == "GET":
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)

        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# -----------------------------------------------------------------------------
# Register - Create user and return tokens
# -----------------------------------------------------------------------------
@extend_schema(request=UserRegistrationSerializer, responses={201: UserSerializer})
class RegisterView(generics.CreateAPIView):
    """
    Create a new user (registration). Uses UserRegistrationSerializer so Swagger shows fields.
    """

    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        # Use serializer.create to create and hash password
        user = serializer.save()
        AuditLog.objects.create(
            user=user,
            action="USER_REGISTERED",
            resource_id=str(user.id),
            meta={"email": user.email},
        )
        self.created_user = user

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        user = getattr(self, "created_user", None)
        refresh = RefreshToken.for_user(user)
        response.data = {
            "user": UserSerializer(user).data,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }
        return response


# -----------------------------------------------------------------------------
# Login - authenticate & return tokens
# -----------------------------------------------------------------------------
@extend_schema(
    request=LoginSerializer,
    responses={
        200: {
            "type": "object",
            "properties": {"access": {"type": "string"}, "refresh": {"type": "string"}},
        }
    },
)
class LoginView(generics.GenericAPIView):
    """
    Login endpoint (email + password). Uses LoginSerializer so Swagger shows request body.
    """

    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        user = authenticate(request, username=email, password=password)
        if not user:
            AuditLog.objects.create(
                action="LOGIN_FAILED",
                meta={"email": email, "ip": request.META.get("REMOTE_ADDR")},
            )
            return Response(
                {"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)
        AuditLog.objects.create(
            user=user,
            action="LOGIN_SUCCESS",
            resource_id=str(user.id),
            meta={"ip": request.META.get("REMOTE_ADDR")},
        )

        return Response(
            {
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK,
        )


# -----------------------------------------------------------------------------
# Child profile viewset
# -----------------------------------------------------------------------------
class ChildProfileViewSet(ModelViewSet):
    """
    Parents manage their children; admins can see all.
    - create: parent is attached from request.user
    - list: parents see only their children
    """

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return (
            ChildProfileCreateSerializer
            if self.action in ("create", "update", "partial_update")
            else ChildProfileSerializer
        )

    def get_queryset(self):
        user = self.request.user
        if getattr(user, "is_admin", False):
            return ChildProfile.objects.all().order_by("-created_at")
        if getattr(user, "is_parent", False):
            return ChildProfile.objects.filter(parent=user).order_by("-created_at")
        return ChildProfile.objects.none()

    def get_serializer_context(self):
        # include request for serializers that need it
        return {"request": self.request}

    def perform_create(self, serializer):
        serializer.save(parent=self.request.user)

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def progress(self, request, pk=None):
        """
        Return progress for a specific child (used by frontend/ML).
        """
        from progress.models import Progress
        from progress.serializers import ProgressSerializer

        child = self.get_object()
        qs = Progress.objects.filter(child=child)
        serializer = ProgressSerializer(qs, many=True)
        return Response(serializer.data)


# -----------------------------------------------------------------------------
# Teacher profile viewset
# -----------------------------------------------------------------------------
class TeacherProfileViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only listing of teacher profiles. Requires authenticated user.
    """

    queryset = TeacherProfile.objects.all().order_by("-created_at")
    serializer_class = TeacherProfileSerializer
    permission_classes = [IsAuthenticated]
