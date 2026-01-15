from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Question, Quiz, QuizAttempt
from .serializers import (
    QuestionSerializer,
    QuizAttemptSerializer,
    QuizAttemptSubmitSerializer,
    QuizSerializer,
)


class QuizViewSet(ModelViewSet):
    """Full CRUD for quizzes"""

    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["id", "title", "lesson"]
    search_fields = ["title"]
    ordering_fields = ["created_at", "title"]

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        - 'list' and 'retrieve' (GET): Allow any logged-in user (Parent/Child).
        - 'create', 'update', 'partial_update', 'destroy': Only Admins.
        """
        if self.action in ["list", "retrieve"]:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]

    def get_serializer_context(self):
        return {"request": self.request}


class QuestionViewSet(ModelViewSet):
    """CRUD for questions within a quiz"""

    serializer_class = QuestionSerializer
    permission_classes = [IsAdminUser]  # Only admin can create/update/delete

    def get_queryset(self):
        return Question.objects.filter(quiz_id=self.kwargs.get("quiz_pk")).order_by(
            "order"
        )

    def get_serializer_context(self):
        return {"quiz_id": self.kwargs.get("quiz_pk")}


class QuizAttemptViewSet(ModelViewSet):
    queryset = QuizAttempt.objects.all().order_by("-created_at")
    serializer_class = QuizAttemptSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["quiz_id", "child_id", "status"]
    search_fields = ["quiz__title"]
    ordering_fields = ["created_at", "score"]

    def get_serializer_context(self):
        return {"request": self.request}

    def get_queryset(self):
        user = self.request.user
        if getattr(user, "is_admin", False):
            return QuizAttempt.objects.all().order_by("-created_at")
        if getattr(user, "is_parent", False):
            from profiles.models import ChildProfile

            children = ChildProfile.objects.filter(parent=user)
            return QuizAttempt.objects.filter(child__in=children).order_by(
                "-created_at"
            )
        return QuizAttempt.objects.none()

    @action(
        detail=False,
        methods=["post"],
        url_path="submit",
        permission_classes=[IsAuthenticated],
    )
    def submit(self, request):
        serializer = QuizAttemptSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        child_id = serializer.validated_data.get("child_id")
        answers = serializer.validated_data.get("answers")
        quiz_id = request.data.get("quiz_id")

        if not quiz_id:
            return Response(
                {"error": "quiz_id required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            quiz = Quiz.objects.get(id=quiz_id)
        except Quiz.DoesNotExist:
            return Response(
                {"error": "quiz not found"}, status=status.HTTP_404_NOT_FOUND
            )

        try:
            from profiles.models import ChildProfile

            child = ChildProfile.objects.get(id=child_id)
        except Exception:
            return Response(
                {"error": "child not found"}, status=status.HTTP_404_NOT_FOUND
            )

        attempt = QuizAttempt.objects.create(
            child=child,
            quiz=quiz,
            answers=answers,
            status=QuizAttempt.Status.IN_PROGRESS,
        )

        attempt.complete_attempt()

        return Response(
            QuizAttemptSerializer(attempt, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )

    def create(self, request, *args, **kwargs):
        return self.submit(request)
