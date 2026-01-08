import pytest
from django.utils.text import slugify

from lessons.models import Collection, Lesson, MediaUpload


@pytest.mark.django_db
def test_collection_slug_and_str():
    c = Collection(title="My First Collection", description="desc")
    c.save()
    if c.slug != slugify("My First Collection"):
        raise AssertionError(
            f"expected slug {slugify('My First Collection')}, got {c.slug}"
        )
    if str(c) != "My First Collection":
        raise AssertionError(f"expected str 'My First Collection', got {str(c)}")


@pytest.mark.django_db
def test_lesson_defaults_and_slug(factory):
    # Pass the profile string as 'profiles.TeacherProfile'
    teacher = factory.make("profiles.TeacherProfile", user__username="teach1")

    lesson = Lesson(
        title="Intro to Testing",
        description="desc",
        video_url="http://example.com/video.mp4",
        teacher=teacher,
    )
    lesson.save()

    if lesson.slug != slugify("Intro to Testing"):
        raise AssertionError(
            f"expected slug {slugify('Intro to Testing')}, got {lesson.slug}"
        )
    if lesson.difficulty != Lesson.Difficulty.EASY:
        raise AssertionError(
            f"expected difficulty {Lesson.Difficulty.EASY}, got {lesson.difficulty}"
        )
    if lesson.tags != []:
        raise AssertionError(f"expected tags [], got {lesson.tags}")
    if lesson.is_published is not False:
        raise AssertionError(f"expected is_published False, got {lesson.is_published}")
    if str(lesson) != f"Intro to Testing by {teacher.user.username}":
        raise AssertionError(
            f"expected str 'Intro to Testing by {teacher.user.username}', got {str(lesson)}"
        )


@pytest.mark.django_db
def test_mediaupload_str_and_default_status(factory):
    teacher = factory.make("profiles.TeacherProfile", user__username="teach2")

    # FIX: Use the 'Lesson' class directly instead of "lesson.Lesson"
    lesson = factory.make(
        Lesson,
        title="Video Lesson",
        teacher=teacher,
        description="d",
        video_url="http://ex.com/v.mp4",
    )

    mu = MediaUpload.objects.create(
        lesson=lesson,
        uploader=teacher.user,
        file_url="http://cdn.example.com/file.mp4",
        file_type=MediaUpload.FileType.VIDEO_MP4,
    )

    if str(mu) != f"{MediaUpload.FileType.VIDEO_MP4} - {mu.status}":
        raise AssertionError(
            f"expected str '{MediaUpload.FileType.VIDEO_MP4} - {mu.status}', got {str(mu)}"
        )
    if mu.status != MediaUpload.Status.PENDING:
        raise AssertionError(
            f"expected status {MediaUpload.Status.PENDING}, got {mu.status}"
        )


@pytest.mark.django_db
def test_mediaupload_deleted_when_lesson_deleted(factory):
    teacher = factory.make("profiles.TeacherProfile", user__username="teach3")

    # FIX: Use 'Lesson' and 'MediaUpload' classes directly
    lesson = factory.make(
        Lesson,
        title="ToBeDeleted",
        teacher=teacher,
        description="d",
        video_url="http://ex.com/v2.mp4",
    )
    mu = factory.make(
        MediaUpload,
        lesson=lesson,
        uploader=teacher.user,
        file_url="http://cdn.example.com/another.mp4",
        file_type=MediaUpload.FileType.VIDEO_MP4,
    )

    pk = mu.pk
    lesson.delete()

    if MediaUpload.objects.filter(pk=pk).exists():
        raise AssertionError(
            f"MediaUpload with pk={pk} still exists after lesson.delete()"
        )
