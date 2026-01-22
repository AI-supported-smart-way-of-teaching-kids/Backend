import pytest
from rest_framework.exceptions import ValidationError
from lessons.serializers import (
    CollectionSerializer,
    MediaUploadSerializer,
    LessonSerializer,
    LessonCreateSerializer,
)
from lessons.models import Collection, Lesson, MediaUpload
from profiles.models import User, TeacherProfile


# ------------------------------
# Fixtures
# ------------------------------
@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="user1", email="user1@test.com", password="pass123"
    )


@pytest.fixture
def teacher_user(db):
    user = User.objects.create_user(
        username="teacher1", email="teacher1@test.com", password="pass123"
    )
    TeacherProfile.objects.create(user=user)
    return user


@pytest.fixture
def collection(db):
    return Collection.objects.create(title="Math Collection")


@pytest.fixture
def lesson(db, teacher_user, collection):
    return Lesson.objects.create(
        title="Lesson 1",
        description="A test lesson",
        video_url="http://example.com/video.mp4",
        duration_seconds=120,
        difficulty="easy",
        teacher=teacher_user.teacher_profile,
        collection=collection,
        tags=["math", "science"],
        is_published=True,
    )


@pytest.fixture
def media_upload(db, teacher_user, lesson):
    return MediaUpload.objects.create(
        lesson=lesson,
        file_url="http://example.com/media.mp4",
        file_type="video/mp4",
        uploader=teacher_user,
        status="pending",
    )


# ------------------------------
# Test CollectionSerializer
# ------------------------------
@pytest.mark.django_db
def test_collection_serializer(collection):
    serializer = CollectionSerializer(collection)
    data = serializer.data
    assert data["title"] == collection.title
    assert "lesson_count" in data
    assert data["lesson_count"] == 0  # no lessons attached yet


# ------------------------------
# Test MediaUploadSerializer
# ------------------------------
@pytest.mark.django_db
def test_media_upload_serializer(media_upload):
    serializer = MediaUploadSerializer(media_upload)
    data = serializer.data
    assert data["file_url"] == media_upload.file_url
    assert data["uploader_username"] == media_upload.uploader.username
    # Read-only fields
    for field in ["id", "status", "uploader", "created_at"]:
        assert field in serializer.Meta.read_only_fields


# ------------------------------
# Test LessonSerializer (for listing)
# ------------------------------
@pytest.mark.django_db
def test_lesson_serializer(lesson, media_upload):
    serializer = LessonSerializer(lesson)
    data = serializer.data
    assert data["title"] == lesson.title
    assert data["teacher_name"] == lesson.teacher.user.username
    assert data["collection_title"] == lesson.collection.title
    # Check nested media
    assert len(data["media_uploads"]) == 1
    assert data["media_uploads"][0]["file_url"] == media_upload.file_url
    # Read-only fields
    for field in ["id", "slug", "created_at", "teacher_name", "media_uploads"]:
        assert field in serializer.Meta.read_only_fields


# ------------------------------
# Test LessonCreateSerializer
# ------------------------------
@pytest.mark.django_db
def test_lesson_create_serializer_success(teacher_user, collection):
    data = {
        "title": "New Lesson",
        "description": "Lesson description",
        "video_url": "http://example.com/video.mp4",
        "duration_seconds": 150,
        "difficulty": "medium",
        "collection": collection.id,
        "tags": ["math", "science"],
        "is_published": True,
    }

    serializer = LessonCreateSerializer(
        data=data, context={"request": type("Request", (), {"user": teacher_user})()}
    )
    assert serializer.is_valid(), serializer.errors
    lesson = serializer.save()
    assert lesson.teacher == teacher_user.teacher_profile
    assert lesson.tags == data["tags"]
    assert lesson.title == data["title"]


@pytest.mark.django_db
def test_lesson_create_serializer_non_teacher(user, collection):
    data = {
        "title": "New Lesson",
        "description": "Lesson description",
        "video_url": "http://example.com/video.mp4",
        "collection": collection.id,
        "tags": ["math"],
        "is_published": True,
    }

    # Mock a request object with the non-teacher user
    mock_request = type("Request", (), {"user": user})()

    serializer = LessonCreateSerializer(data=data, context={"request": mock_request})

    # Validate the input first
    assert serializer.is_valid(), serializer.errors  # should pass basic validation

    # Saving triggers create() where the teacher check happens
    with pytest.raises(ValidationError) as exc_info:
        serializer.save()

    # Ensure the error message is correct
    assert "Only teachers can create lessons." in str(exc_info.value.detail)


@pytest.mark.django_db
def test_lesson_create_serializer_missing_video_url(teacher_user, collection):
    data = {
        "title": "No Video",
        "description": "Lesson description",
        "collection": collection.id,
        "tags": ["math"],
        "is_published": True,
    }
    serializer = LessonCreateSerializer(
        data=data, context={"request": type("Request", (), {"user": teacher_user})()}
    )
    with pytest.raises(ValidationError) as exc_info:
        serializer.is_valid(raise_exception=True)
    assert "video_url" in str(exc_info.value.detail)
