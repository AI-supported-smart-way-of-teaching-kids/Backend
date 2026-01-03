from rest_framework import serializers
from .models import Question, Quiz, QuizAttempt


# =========================
# Question Serializer
# =========================
class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = [
            "id",
            "question_type",
            "question_text",
            "media_url",
            "options",
            "correct_option_index",
            "explanation",
            "order",
        ]
        read_only_fields = ["id"]


# =========================
# Quiz Serializer (Updated for Integration)
# =========================
class QuizSerializer(serializers.ModelSerializer):
    # REMOVED read_only=True so Swagger allows POSTing questions
    questions = QuestionSerializer(many=True)
    lesson_title = serializers.CharField(source="lesson.title", read_only=True)

    class Meta:
        model = Quiz
        fields = [
            "id",
            "lesson",
            "lesson_title",
            "title",
            "time_limit_seconds",
            "questions",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def create(self, validated_data):
        """
        Logic to create Quiz and Questions in one request
        """
        # 1. Extract the questions list from the data
        questions_data = validated_data.pop("questions")

        # 2. Create the main Quiz object
        quiz = Quiz.objects.create(**validated_data)

        # 3. Create each Question linked to this Quiz
        for question_data in questions_data:
            Question.objects.create(quiz=quiz, **question_data)

        return quiz


# =========================
# Quiz Attempt Serializers
# =========================
class QuizAttemptSerializer(serializers.ModelSerializer):
    child_nickname = serializers.CharField(source="child.nickname", read_only=True)
    quiz_title = serializers.CharField(source="quiz.title", read_only=True)

    class Meta:
        model = QuizAttempt
        fields = [
            "id",
            "child",
            "child_nickname",
            "quiz",
            "quiz_title",
            "answers",
            "score",
            "status",
            "duration_seconds",
            "correct_count",
            "total_questions",
            "created_at",
            "completed_at",
        ]
        read_only_fields = [
            "id",
            "score",
            "status",
            "correct_count",
            "total_questions",
            "created_at",
            "completed_at",
        ]


class QuizAttemptSubmitSerializer(serializers.Serializer):
    answers = serializers.ListField(
        child=serializers.DictField(), help_text="List of answers"
    )
    child_id = serializers.IntegerField()

    def validate_answers(self, value):
        if not value:
            raise serializers.ValidationError("Answers cannot be empty")
        return value
