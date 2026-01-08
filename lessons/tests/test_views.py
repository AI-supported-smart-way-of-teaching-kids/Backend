# bandit: skip-file

import pytest
from django.urls import reverse
from rest_framework import status


# ------------------------------
# Test: Public collections can be listed
# ------------------------------
@pytest.mark.django_db
def test_collection_list_public(api_client, factory):
    # Create two collections
    factory.make("lessons.Collection", title="Math")
    factory.make("lessons.Collection", title="Science")

    # Call the collection list API endpoint
    url = reverse("collection-list")
    response = api_client.get(url)

    # Support both paginated and non-paginated responses
    data = response.data
    if isinstance(data, dict):
        # paginated response - assert count and results length
        assert data.get("count", 0) == 2
        results = data.get("results", [])
        assert len(results) == 2
    else:
        # plain list response
        assert len(data) == 2

    assert response.status_code == status.HTTP_200_OK


# ------------------------------
# Test: Public lessons can be listed
# ------------------------------
@pytest.mark.django_db
def test_lesson_list_public(api_client, factory):
    # Create two published lessons
    factory.make("lessons.Lesson", title="Lesson 1", is_published=True)
    factory.make("lessons.Lesson", title="Lesson 2", is_published=True)

    # Call the lesson list API endpoint
    url = reverse("lesson-list")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK


# ------------------------------
# Test: Normal user cannot create a lesson
# ------------------------------
@pytest.mark.django_db
def test_lesson_create_denied_for_normal_user(factory, auth_client, parent_user):
    # parent_user is used as a normal (non-teacher) user
    collection = factory.make("lessons.Collection")

    url = reverse("lesson-list")
    payload = {
        "title": "New Lesson",
        "description": "Test",
        "collection": collection.id,
        "difficulty": "easy",
        "is_published": True,
    }

    client = auth_client(parent_user)  # call factory to get authenticated client
    response = client.post(url, payload)

    # Expect forbidden status since normal users cannot create lessons
    assert response.status_code == status.HTTP_403_FORBIDDEN


# ------------------------------
# Test: Other teachers cannot upload media to lessons they don't own
# ------------------------------
@pytest.mark.django_db
def test_lesson_create_allowed_for_teacher_view(factory, auth_client, teacher_user):
    # Ensure teacher profile exists
    if not hasattr(teacher_user, "teacherprofile"):
        factory.make("profiles.TeacherProfile", user=teacher_user)

    collection = factory.make("lessons.Collection")

    url = reverse("lesson-list")
    payload = {
        "title": "Teacher Lesson",
        "description": "Allowed",
        "collection": collection.id,
        "difficulty": "easy",
        "is_published": True,
        "video_url": "http://example.com/video.mp4",  # required field
        "thumbnail_url": "http://example.com/thumb.jpg",  # optional but good to include
        "duration_seconds": 300,  # optional
        "tags": ["math", "science"],  # optional
    }

    client = auth_client(teacher_user)
    response = client.post(url, payload)

    assert response.status_code == status.HTTP_201_CREATED, (
        "Expected 201 Created — got 400 Bad Request. "
        f"Response data: {getattr(response, 'data', 'no-data')}"
    )


# ------------------------------
# Test: Track lesson progress successfully
# ------------------------------
@pytest.mark.django_db
def test_track_progress_success(factory, auth_client, parent_user):
    lesson = factory.make("lessons.Lesson")
    child = factory.make("profiles.ChildProfile")

    url = reverse("lesson-track-progress", args=[lesson.id])
    payload = {
        "child_id": child.id,
        "completion_status": True,
        "time_spent": 120,  # in seconds
        "video_watch_percentage": 80,
        "number_of_clicks": 5,
    }

    client = auth_client(parent_user)
    response = client.post(url, payload)

    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("detail") == "Progress tracked"


# ------------------------------
# Test: Track progress fails if child_id missing
# ------------------------------
@pytest.mark.django_db
def test_track_progress_missing_child_id(factory, auth_client, parent_user):
    lesson = factory.make("lessons.Lesson")

    url = reverse("lesson-track-progress", args=[lesson.id])
    client = auth_client(parent_user)
    response = client.post(url, {})  # missing child_id

    assert response.status_code == status.HTTP_400_BAD_REQUEST


# ------------------------------
# Test: Users can only list their own media uploads
# ------------------------------
@pytest.mark.django_db
def test_media_upload_list_only_user_files(factory, auth_client, teacher_user):
    # use teacher_user as the uploader (or switch to parent_user if you prefer)
    _ = factory.make("lessons.MediaUpload", uploader=teacher_user)
    _ = factory.make("lessons.MediaUpload")  # other user

    url = reverse("mediaupload-list")
    client = auth_client(teacher_user)
    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK

    data = response.data
    if isinstance(data, dict):
        results = data.get("results", [])
        assert len(results) == 1
    else:
        assert len(data) == 1
