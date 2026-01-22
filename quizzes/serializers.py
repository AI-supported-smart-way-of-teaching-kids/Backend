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
        questions_data = validated_data.pop("questions")
        quiz = Quiz.objects.create(**validated_data)

        for question_data in questions_data:
            Question.objects.create(quiz=quiz, **question_data)

        return quiz

    def update(self, instance, validated_data):
        questions_data = validated_data.pop("questions", [])

        # 1️⃣ Update quiz fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # 2️⃣ Existing questions map
        existing_questions = {q.id: q for q in instance.questions.all()}

        sent_question_ids = []

        # 3️⃣ Update or create questions
        for question_data in questions_data:
            question_id = question_data.get("id")

            if question_id and question_id in existing_questions:
                question = existing_questions[question_id]
                for attr, value in question_data.items():
                    setattr(question, attr, value)
                question.save()
                sent_question_ids.append(question_id)
            else:
                new_question = Question.objects.create(quiz=instance, **question_data)
                sent_question_ids.append(new_question.id)

        # 4️⃣ Delete removed questions
        for q_id, q_obj in existing_questions.items():
            if q_id not in sent_question_ids:
                q_obj.delete()

        return instance


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
    child_id = serializers.UUIDField()

    def validate_answers(self, value):
        if not value:
            raise serializers.ValidationError("Answers cannot be empty")
        return value
