# Lesson Creation & Media Upload Flow Analysis

## 📋 Executive Summary

The current implementation uses a **two-step process**: 
1. Create lesson metadata (JSON) → returns `lesson.id`
2. Upload media files (multipart/form-data) → links to `lesson.id`

**Key Finding:** There's architectural confusion between `Lesson.video_url` (S3/CDN URL) and `MediaUpload` (local file storage). The API supports both but they serve different purposes.

---

## 🔄 Current API Flow (Step-by-Step)

### **Step 1: Create Lesson Metadata**

**Endpoint:** `POST /api/lessons/lessons/`

**Request:**
```http
POST /api/lessons/lessons/
Content-Type: application/json
Authorization: Bearer {jwt_token}

{
  "title": "Introduction to Numbers",
  "description": "Learn numbers 1-10",
  "video_url": "https://s3.amazonaws.com/bucket/video.mp4",  // ⚠️ REQUIRED
  "thumbnail_url": "https://s3.amazonaws.com/bucket/thumb.jpg",  // Optional
  "duration_seconds": 300,
  "difficulty": "easy",
  "collection": 1,  // Optional collection ID
  "tags": ["math", "numbers", "KG1"],
  "is_published": false
}
```

**Response (201 Created):**
```json
{
  "id": 42,
  "title": "Introduction to Numbers",
  "slug": "introduction-to-numbers",
  "description": "Learn numbers 1-10",
  "video_url": "https://s3.amazonaws.com/bucket/video.mp4",
  "thumbnail_url": "https://s3.amazonaws.com/bucket/thumb.jpg",
  "duration_seconds": 300,
  "difficulty": "easy",
  "collection": 1,
  "tags": ["math", "numbers", "KG1"],
  "is_published": false
}
```

**Backend Behavior:**
- Uses `LessonCreateSerializer` 
- Validates `video_url` is required
- Auto-attaches `teacher` from `request.user.teacher_profile`
- Auto-generates `slug` from title
- Returns lesson `id` for next step

---

### **Step 2: Upload Media Files (Separate Call)**

**Endpoint:** `POST /api/lessons/media-uploads/`

**Request:**
```http
POST /api/lessons/media-uploads/
Content-Type: multipart/form-data
Authorization: Bearer {jwt_token}

Form Data:
  lesson: 42                    // ⚠️ Lesson ID from Step 1
  file: [binary file]          // ⚠️ Actual file (video/image/audio)
  file_type: "video/mp4"       // ⚠️ MIME type (client-controlled - SECURITY RISK)
```

**Response (201 Created):**
```json
{
  "id": 123,
  "lesson": 42,
  "file": "/media/videos/myfile.mp4",
  "file_url": "",  // Empty if local storage
  "file_type": "video/mp4",
  "status": "pending",  // pending → processing → done/failed
  "uploader": 5,
  "uploader_username": "teacher_john",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Backend Behavior:**
- Uses `MediaUploadSerializer`
- Validates teacher owns the lesson
- Saves file to `media/videos/`, `media/images/`, or `media/audios/` based on `file_type`
- Sets `status = "pending"` (may be processed async later)
- Uploader auto-set from `request.user`

---

## ⚠️ Architectural Issues & Confusion

### **1. Dual Video URL System**

**Problem:** Lesson has two video-related fields:
- `Lesson.video_url` - S3/CDN URL (required during creation)
- `MediaUpload.file` - Local file storage (uploaded separately)

**Question:** When should frontend use which?

**Analysis:**
- `video_url` = External/existing video (e.g., YouTube, S3)
- `MediaUpload` = New file uploads to backend server

**Confusion:** If you upload via `MediaUpload`, you still need to provide `video_url` when creating lesson. This is contradictory.

---

### **2. Two-Step Process Creates UX Complexity**

**Issues:**
1. User must wait for lesson creation before uploading media
2. If media upload fails, lesson exists without media
3. No atomic transaction (lesson can exist without media)
4. Frontend must handle partial failures

**Recommendation:** Support single-step creation with optional media uploads.

---

### **3. File Type Security Risk**

**Location:** `lessons/views.py:214`, `lessons/models.py:153`

**Problem:** `file_type` is **client-controlled**:
```python
file_type: "video/mp4"  # Client sends this - NOT validated from actual file
```

**Risk:** Client can send `file_type: "image/png"` but upload a malicious `.exe` file.

**Fix Needed:**
```python
# Backend should determine MIME type from file content
import magic  # python-magic library

def perform_create(self, serializer):
    # ...
    uploaded_file = request.FILES['file']
    
    # Verify MIME type from file content (not client)
    mime = magic.Magic(mime=True)
    actual_mime_type = mime.from_buffer(uploaded_file.read(1024))
    uploaded_file.seek(0)  # Reset file pointer
    
    # Validate against allowed types
    allowed_types = ['video/mp4', 'video/webm', 'image/png', 'image/jpg', 'audio/mpeg']
    if actual_mime_type not in allowed_types:
        raise ValidationError(f"File type {actual_mime_type} not allowed")
    
    serializer.save(uploader=user, file_type=actual_mime_type)  # Use verified type
```

---

### **4. Missing File Size Validation**

**Problem:** No maximum file size limit.

**Risk:** DoS via large file uploads.

**Fix Needed:**
```python
# In serializer or view
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

def validate_file(self, value):
    if value.size > MAX_FILE_SIZE:
        raise ValidationError(f'File exceeds {MAX_FILE_SIZE / 1024 / 1024}MB limit')
    return value
```

---

### **5. Media Upload Status Not Polled**

**Problem:** Media upload starts with `status: "pending"` but no endpoint to check processing status.

**Frontend Impact:** Can't show progress or handle failures.

---

## 📱 Frontend Integration Guide

### **Recommended Workflow for Frontend**

#### **Option A: External Video (Use S3/CDN URL)**

Use when video is already hosted externally:

```javascript
// Step 1: Create lesson with video_url
const createLesson = async (lessonData) => {
  const response = await fetch('/api/lessons/lessons/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      title: lessonData.title,
      description: lessonData.description,
      video_url: lessonData.videoUrl,  // S3/CDN URL
      thumbnail_url: lessonData.thumbnailUrl,
      difficulty: lessonData.difficulty,
      collection: lessonData.collectionId,
      tags: lessonData.tags,
      is_published: lessonData.isPublished
    })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create lesson');
  }
  
  return await response.json();
};
```

**✅ Single API call, no file upload needed**

---

#### **Option B: Upload Files to Backend (Use MediaUpload)**

Use when uploading new files:

```javascript
// Step 1: Create lesson (video_url can be placeholder or empty)
const createLessonWithPlaceholder = async (lessonData) => {
  const response = await fetch('/api/lessons/lessons/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      title: lessonData.title,
      description: lessonData.description,
      video_url: 'https://placeholder.com/video.mp4',  // ⚠️ Required but can be placeholder
      difficulty: lessonData.difficulty,
      collection: lessonData.collectionId,
      tags: lessonData.tags,
      is_published: false  // Don't publish until media is uploaded
    })
  });
  
  const lesson = await response.json();
  return lesson.id;  // Return lesson ID for next step
};

// Step 2: Upload media files
const uploadMedia = async (lessonId, file, fileType) => {
  const formData = new FormData();
  formData.append('lesson', lessonId);
  formData.append('file', file);
  formData.append('file_type', fileType);  // e.g., "video/mp4"
  
  const response = await fetch('/api/lessons/media-uploads/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
      // ⚠️ Don't set Content-Type - browser sets it with boundary
    },
    body: formData
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to upload media');
  }
  
  return await response.json();
};

// Step 3: Update lesson.video_url after upload completes
const updateLessonVideoUrl = async (lessonId, mediaUploadUrl) => {
  const response = await fetch(`/api/lessons/lessons/${lessonId}/`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      video_url: mediaUploadUrl  // Use the uploaded file URL
    })
  });
  
  return await response.json();
};

// Combined workflow
const createLessonWithUpload = async (lessonData, videoFile, thumbnailFile) => {
  try {
    // Step 1: Create lesson
    const lessonId = await createLessonWithPlaceholder(lessonData);
    
    // Step 2: Upload video
    const videoUpload = await uploadMedia(lessonId, videoFile, 'video/mp4');
    
    // Step 3: Upload thumbnail (optional)
    let thumbnailUpload = null;
    if (thumbnailFile) {
      thumbnailUpload = await uploadMedia(lessonId, thumbnailFile, 'image/png');
    }
    
    // Step 4: Update lesson with actual URLs
    const updatedLesson = await updateLessonVideoUrl(
      lessonId, 
      videoUpload.file || `/media/${videoUpload.file}`
    );
    
    // Step 5: Update thumbnail URL if uploaded
    if (thumbnailUpload) {
      await fetch(`/api/lessons/lessons/${lessonId}/`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          thumbnail_url: thumbnailUpload.file || `/media/${thumbnailUpload.file}`
        })
      });
    }
    
    return updatedLesson;
    
  } catch (error) {
    // Handle errors - lesson may be partially created
    console.error('Failed to create lesson with upload:', error);
    throw error;
  }
};
```

---

### **React Component Example**

```jsx
import React, { useState } from 'react';

const LessonCreateForm = () => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    difficulty: 'easy',
    tags: [],
    videoFile: null,
    thumbnailFile: null
  });
  const [uploadProgress, setUploadProgress] = useState(0);
  const [loading, setLoading] = useState(false);
  
  const handleFileChange = (e, field) => {
    setFormData({ ...formData, [field]: e.target.files[0] });
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setUploadProgress(0);
    
    try {
      // Create lesson first
      const lessonResponse = await fetch('/api/lessons/lessons/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          title: formData.title,
          description: formData.description,
          video_url: 'https://placeholder.com/video.mp4',  // Placeholder
          difficulty: formData.difficulty,
          tags: formData.tags,
          is_published: false
        })
      });
      
      const lesson = await lessonResponse.json();
      setUploadProgress(25);
      
      // Upload video file
      if (formData.videoFile) {
        const videoFormData = new FormData();
        videoFormData.append('lesson', lesson.id);
        videoFormData.append('file', formData.videoFile);
        videoFormData.append('file_type', formData.videoFile.type);
        
        const uploadResponse = await fetch('/api/lessons/media-uploads/', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          },
          body: videoFormData
        });
        
        const videoUpload = await uploadResponse.json();
        setUploadProgress(75);
        
        // Update lesson with actual file URL
        await fetch(`/api/lessons/lessons/${lesson.id}/`, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            video_url: videoUpload.file || `/media/${videoUpload.file}`
          })
        });
      }
      
      setUploadProgress(100);
      alert('Lesson created successfully!');
      
    } catch (error) {
      console.error('Error:', error);
      alert('Failed to create lesson');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        placeholder="Lesson Title"
        value={formData.title}
        onChange={(e) => setFormData({ ...formData, title: e.target.value })}
        required
      />
      
      <textarea
        placeholder="Description"
        value={formData.description}
        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
        required
      />
      
      <input
        type="file"
        accept="video/mp4,video/webm"
        onChange={(e) => handleFileChange(e, 'videoFile')}
      />
      
      <input
        type="file"
        accept="image/png,image/jpg"
        onChange={(e) => handleFileChange(e, 'thumbnailFile')}
      />
      
      {loading && (
        <div>
          <progress value={uploadProgress} max="100" />
          <span>{uploadProgress}%</span>
        </div>
      )}
      
      <button type="submit" disabled={loading}>
        Create Lesson
      </button>
    </form>
  );
};
```

---

## 🎯 Recommended Backend Improvements

### **1. Support Single-Step Creation (Recommended)**

Add ability to create lesson with media in one request:

```python
# New serializer
class LessonCreateWithMediaSerializer(serializers.ModelSerializer):
    video_file = serializers.FileField(required=False, write_only=True)
    thumbnail_file = serializers.ImageField(required=False, write_only=True)
    
    class Meta:
        model = Lesson
        fields = [..., 'video_file', 'thumbnail_file']
    
    def create(self, validated_data):
        video_file = validated_data.pop('video_file', None)
        thumbnail_file = validated_data.pop('thumbnail_file', None)
        
        lesson = super().create(validated_data)
        
        # Create MediaUpload for video
        if video_file:
            MediaUpload.objects.create(
                lesson=lesson,
                file=video_file,
                file_type=self._detect_mime_type(video_file),
                uploader=self.context['request'].user,
                status='pending'
            )
        
        return lesson
```

---

### **2. Make video_url Optional During Creation**

Allow creating lesson without video_url, then update after media upload:

```python
# In LessonCreateSerializer
video_url = serializers.URLField(required=False, allow_blank=True)

def validate(self, attrs):
    # Only require video_url if no media file is being uploaded
    if not attrs.get('video_url') and not self.context.get('request').FILES:
        raise serializers.ValidationError({
            "video_url": "video_url or media file is required."
        })
    return attrs
```

---

### **3. Add Media Upload Status Endpoint**

```python
@action(detail=True, methods=['get'])
def media_status(self, request, pk=None):
    lesson = self.get_object()
    uploads = lesson.media_uploads.all()
    
    return Response({
        'lesson_id': lesson.id,
        'media_uploads': MediaUploadSerializer(uploads, many=True).data
    })
```

---

### **4. Add File Validation to Serializer**

```python
class MediaUploadSerializer(serializers.ModelSerializer):
    # ...
    
    def validate_file(self, value):
        # Size validation
        MAX_SIZE = 100 * 1024 * 1024  # 100MB
        if value.size > MAX_SIZE:
            raise serializers.ValidationError(
                f'File size exceeds {MAX_SIZE / 1024 / 1024}MB'
            )
        
        # Type validation (from file content)
        import magic
        mime = magic.Magic(mime=True)
        actual_type = mime.from_buffer(value.read(1024))
        value.seek(0)
        
        allowed = ['video/mp4', 'video/webm', 'image/png', 'image/jpg', 'audio/mpeg']
        if actual_type not in allowed:
            raise serializers.ValidationError(f'File type {actual_type} not allowed')
        
        return value
```

---

## 📊 API Endpoint Summary

| Endpoint | Method | Purpose | Content-Type |
|----------|--------|---------|--------------|
| `/api/lessons/lessons/` | POST | Create lesson metadata | `application/json` |
| `/api/lessons/lessons/{id}/` | GET | Get lesson (includes media_uploads) | - |
| `/api/lessons/lessons/{id}/` | PATCH | Update lesson (e.g., video_url) | `application/json` |
| `/api/lessons/media-uploads/` | POST | Upload media file | `multipart/form-data` |
| `/api/lessons/media-uploads/{id}/` | GET | Get media upload status | - |

---

## 🔒 Security Checklist for Frontend

1. ✅ Validate file types client-side (but don't trust - backend must verify)
2. ✅ Show file size limit before upload
3. ✅ Handle upload progress/errors gracefully
4. ✅ Don't expose backend errors to users (sanitize)
5. ✅ Validate lesson ownership before allowing uploads
6. ✅ Use HTTPS for all requests (especially file uploads)

---

## 🚀 Quick Integration Checklist

- [ ] **Step 1:** Create lesson with placeholder `video_url`
- [ ] **Step 2:** Upload video file via `POST /api/lessons/media-uploads/`
- [ ] **Step 3:** Upload thumbnail file (optional)
- [ ] **Step 4:** Update lesson `video_url` and `thumbnail_url` with uploaded file paths
- [ ] **Step 5:** Set `is_published = true` when ready
- [ ] **Error Handling:** Handle partial failures (cleanup lesson if upload fails)

---

**Generated:** 2024-01-XX  
**Status:** Current implementation requires two-step process; improvements recommended for single-step flow.
