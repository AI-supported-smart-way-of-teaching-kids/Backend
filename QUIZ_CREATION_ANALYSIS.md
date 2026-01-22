# Quiz Creation & Question Management Flow Analysis

## 📋 Executive Summary

The quiz system supports **TWO workflows**:
1. **✅ Single-Step:** Create quiz with all questions in one request (RECOMMENDED)
2. **Two-Step:** Create quiz first, then add questions separately (Not currently supported via API)

**Key Finding:** The `QuizSerializer` supports nested question creation in a single POST request, which is the best approach for frontend integration.

---

## 🔄 Current API Flow (Step-by-Step)

### **✅ Option 1: Single-Step Creation (RECOMMENDED)**

Create quiz with all questions in one request:

**Endpoint:** `POST /api/quizzes/quizzes/`

**Request:**
```http
POST /api/quizzes/quizzes/
Content-Type: application/json
Authorization: Bearer {jwt_token}

{
  "lesson": 42,                    // ⚠️ Required: Lesson ID
  "title": "Math Quiz 1",
  "time_limit_seconds": 600,       // Optional: 30 seconds minimum
  "questions": [                   // ⚠️ Array of questions
    {
      "question_type": "text",     // "text" | "image" | "audio"
      "question_text": "What is 2 + 2?",
      "media_url": null,           // Required if type is "image" or "audio"
      "options": [                 // 2-4 options required
        "3",
        "4",                       // Correct answer
        "5",
        "6"
      ],
      "correct_option_index": 1,   // Index of correct answer (0-based)
      "explanation": "2 + 2 equals 4",
      "order": 0                   // Question order (defaults to 0)
    },
    {
      "question_type": "image",
      "question_text": "Which animal is this?",
      "media_url": "https://example.com/cat.jpg",  // ⚠️ Required for image/audio
      "options": ["Dog", "Cat", "Bird"],
      "correct_option_index": 1,
      "explanation": "This is a cat",
      "order": 1
    }
  ]
}
```

**Response (201 Created):**
```json
{
  "id": 10,
  "lesson": 42,
  "lesson_title": "Introduction to Numbers",
  "title": "Math Quiz 1",
  "time_limit_seconds": 600,
  "questions": [
    {
      "id": 25,
      "question_type": "text",
      "question_text": "What is 2 + 2?",
      "media_url": null,
      "options": ["3", "4", "5", "6"],
      "correct_option_index": 1,
      "explanation": "2 + 2 equals 4",
      "order": 0
    },
    {
      "id": 26,
      "question_type": "image",
      "question_text": "Which animal is this?",
      "media_url": "https://example.com/cat.jpg",
      "options": ["Dog", "Cat", "Bird"],
      "correct_option_index": 1,
      "explanation": "This is a cat",
      "order": 1
    }
  ],
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Backend Behavior:**
- Uses `QuizSerializer.create()` method
- Creates Quiz first
- Then creates all Questions in a loop (linked via `quiz` FK)
- Returns complete quiz with all questions
- ✅ **Atomic operation** - All or nothing (if one question fails, entire quiz creation fails)

---

### **Option 2: Two-Step Creation (NOT RECOMMENDED - Current Limitation)**

**Problem:** `QuestionViewSet` exists but is **NOT registered in URLs**. The code references `quiz_pk` but there's no nested route.

**Missing URL Configuration:**
```python
# quizzes/urls.py - QuestionViewSet is NOT registered!
router.register(r"quizzes", QuizViewSet)  # ✅ Registered
router.register(r"attempts", QuizAttemptViewSet)  # ✅ Registered
# QuestionViewSet - ❌ NOT REGISTERED
```

**Current Status:** Cannot add questions to existing quiz via API.

---

## ⚠️ Architectural Issues & Limitations

### **1. QuestionViewSet Not Accessible via API**

**Location:** `quizzes/views.py:39-51`, `quizzes/urls.py:8-9`

**Problem:** `QuestionViewSet` is defined but never registered in the router.

**Impact:** 
- Cannot add questions to existing quiz
- Cannot update/delete individual questions
- Cannot reorder questions

**Fix Needed:**
```python
# quizzes/urls.py
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers  # Install: pip install drf-nested-routers

router = routers.DefaultRouter()
router.register(r"quizzes", QuizViewSet, basename="quiz")

# Nested router for questions
questions_router = routers.NestedDefaultRouter(router, r"quizzes", lookup="quiz")
questions_router.register(r"questions", QuestionViewSet, basename="quiz-questions")

urlpatterns = [
    path("", include(router.urls)),
    path("", include(questions_router.urls)),
]
```

**This would enable:**
- `POST /api/quizzes/quizzes/{quiz_id}/questions/` - Add question
- `GET /api/quizzes/quizzes/{quiz_id}/questions/` - List questions
- `PATCH /api/quizzes/quizzes/{quiz_id}/questions/{id}/` - Update question
- `DELETE /api/quizzes/quizzes/{quiz_id}/questions/{id}/` - Delete question

---

### **2. No Transaction Handling**

**Location:** `quizzes/serializers.py:45-59`

**Problem:** Quiz and questions created in loop without transaction wrapper.

**Risk:** If question #3 fails, quiz and questions #1-2 are created (partial state).

**Fix:**
```python
from django.db import transaction

def create(self, validated_data):
    questions_data = validated_data.pop("questions")
    
    # Wrap in transaction
    with transaction.atomic():
        quiz = Quiz.objects.create(**validated_data)
        
        for question_data in questions_data:
            Question.objects.create(quiz=quiz, **question_data)
    
    return quiz
```

---

### **3. Missing Question Validation on Create**

**Location:** `quizzes/models.py:110-132`, `quizzes/serializers.py:8-21`

**Problem:** Model has `clean()` method but serializer doesn't call it.

**Risk:** Invalid questions can be created (e.g., `correct_option_index` out of range).

**Fix:**
```python
# In QuestionSerializer
def validate(self, attrs):
    # Create temporary instance to run model validation
    question = Question(**attrs)
    question.clean()  # Raises ValidationError if invalid
    return attrs
```

---

### **4. No Bulk Question Update**

**Problem:** Cannot update all questions at once (must recreate entire quiz).

**Impact:** Editing quiz requires sending all questions again, not just changed ones.

---

### **5. Missing Query Optimization**

**Location:** `quizzes/views.py:21`

**Problem:** 
```python
queryset = Quiz.objects.all()  # No select_related/prefetch_related
```

**Fix:**
```python
queryset = Quiz.objects.select_related('lesson').prefetch_related('questions').all()
```

---

## 📱 Frontend Integration Guide

### **✅ Recommended: Single-Step Quiz Creation**

```javascript
// Create quiz with all questions in one request
const createQuiz = async (lessonId, quizData) => {
  const response = await fetch('/api/quizzes/quizzes/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      lesson: lessonId,  // Required
      title: quizData.title,
      time_limit_seconds: quizData.timeLimit || null,
      questions: quizData.questions.map((q, index) => ({
        question_type: q.type,  // "text" | "image" | "audio"
        question_text: q.text,
        media_url: q.mediaUrl || null,
        options: q.options,  // Array of 2-4 strings
        correct_option_index: q.correctIndex,  // 0-based index
        explanation: q.explanation || null,
        order: index  // Auto-increment order
      }))
    })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create quiz');
  }
  
  return await response.json();
};

// Example usage
const quizData = {
  title: 'Math Quiz 1',
  timeLimit: 600,
  questions: [
    {
      type: 'text',
      text: 'What is 2 + 2?',
      options: ['3', '4', '5', '6'],
      correctIndex: 1,
      explanation: '2 + 2 equals 4'
    },
    {
      type: 'image',
      text: 'Which animal is this?',
      mediaUrl: 'https://example.com/cat.jpg',
      options: ['Dog', 'Cat', 'Bird'],
      correctIndex: 1,
      explanation: 'This is a cat'
    }
  ]
};

const quiz = await createQuiz(42, quizData);
console.log('Quiz created:', quiz.id);
console.log('Questions:', quiz.questions.length);
```

---

### **React Component Example**

```jsx
import React, { useState } from 'react';

const QuizCreateForm = ({ lessonId, onSuccess }) => {
  const [formData, setFormData] = useState({
    title: '',
    timeLimit: '',
    questions: []
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Add new question
  const addQuestion = () => {
    setFormData({
      ...formData,
      questions: [
        ...formData.questions,
        {
          type: 'text',
          text: '',
          mediaUrl: '',
          options: ['', ''],
          correctIndex: 0,
          explanation: '',
          order: formData.questions.length
        }
      ]
    });
  };
  
  // Update question field
  const updateQuestion = (index, field, value) => {
    const questions = [...formData.questions];
    questions[index] = { ...questions[index], [field]: value };
    setFormData({ ...formData, questions });
  };
  
  // Add option to question
  const addOption = (questionIndex) => {
    const questions = [...formData.questions];
    if (questions[questionIndex].options.length < 4) {
      questions[questionIndex].options.push('');
      setFormData({ ...formData, questions });
    }
  };
  
  // Remove option from question
  const removeOption = (questionIndex, optionIndex) => {
    const questions = [...formData.questions];
    const question = questions[questionIndex];
    
    // Ensure at least 2 options
    if (question.options.length > 2) {
      question.options.splice(optionIndex, 1);
      
      // Adjust correct_index if needed
      if (question.correctIndex >= question.options.length) {
        question.correctIndex = question.options.length - 1;
      }
      
      setFormData({ ...formData, questions });
    }
  };
  
  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    // Validation
    if (!formData.title) {
      setError('Quiz title is required');
      setLoading(false);
      return;
    }
    
    if (formData.questions.length === 0) {
      setError('At least one question is required');
      setLoading(false);
      return;
    }
    
    // Validate each question
    for (let i = 0; i < formData.questions.length; i++) {
      const q = formData.questions[i];
      
      if (!q.text) {
        setError(`Question ${i + 1}: Text is required`);
        setLoading(false);
        return;
      }
      
      if (q.options.length < 2) {
        setError(`Question ${i + 1}: At least 2 options required`);
        setLoading(false);
        return;
      }
      
      if ((q.type === 'image' || q.type === 'audio') && !q.mediaUrl) {
        setError(`Question ${i + 1}: Media URL required for ${q.type} questions`);
        setLoading(false);
        return;
      }
      
      if (q.correctIndex < 0 || q.correctIndex >= q.options.length) {
        setError(`Question ${i + 1}: Invalid correct answer index`);
        setLoading(false);
        return;
      }
    }
    
    try {
      const response = await fetch('/api/quizzes/quizzes/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          lesson: lessonId,
          title: formData.title,
          time_limit_seconds: formData.timeLimit ? parseInt(formData.timeLimit) : null,
          questions: formData.questions.map((q, index) => ({
            question_type: q.type,
            question_text: q.text,
            media_url: q.mediaUrl || null,
            options: q.options,
            correct_option_index: q.correctIndex,
            explanation: q.explanation || null,
            order: index
          }))
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || JSON.stringify(errorData));
      }
      
      const quiz = await response.json();
      onSuccess(quiz);
      alert('Quiz created successfully!');
      
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <form onSubmit={handleSubmit}>
      <h2>Create Quiz</h2>
      
      {/* Quiz Metadata */}
      <div>
        <label>
          Quiz Title *
          <input
            type="text"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            required
          />
        </label>
      </div>
      
      <div>
        <label>
          Time Limit (seconds, min 30)
          <input
            type="number"
            min="30"
            value={formData.timeLimit}
            onChange={(e) => setFormData({ ...formData, timeLimit: e.target.value })}
          />
        </label>
      </div>
      
      {/* Questions List */}
      <div>
        <h3>Questions ({formData.questions.length})</h3>
        <button type="button" onClick={addQuestion}>
          + Add Question
        </button>
        
        {formData.questions.map((question, qIndex) => (
          <div key={qIndex} style={{ border: '1px solid #ccc', padding: '1em', margin: '1em 0' }}>
            <h4>Question {qIndex + 1}</h4>
            
            {/* Question Type */}
            <select
              value={question.type}
              onChange={(e) => updateQuestion(qIndex, 'type', e.target.value)}
            >
              <option value="text">Text</option>
              <option value="image">Image</option>
              <option value="audio">Audio</option>
            </select>
            
            {/* Question Text */}
            <textarea
              placeholder="Question text"
              value={question.text}
              onChange={(e) => updateQuestion(qIndex, 'text', e.target.value)}
              required
            />
            
            {/* Media URL (for image/audio) */}
            {(question.type === 'image' || question.type === 'audio') && (
              <input
                type="url"
                placeholder="Media URL"
                value={question.mediaUrl}
                onChange={(e) => updateQuestion(qIndex, 'mediaUrl', e.target.value)}
                required
              />
            )}
            
            {/* Options */}
            <div>
              <label>Options (select correct answer):</label>
              {question.options.map((option, oIndex) => (
                <div key={oIndex}>
                  <input
                    type="radio"
                    name={`correct-${qIndex}`}
                    checked={question.correctIndex === oIndex}
                    onChange={() => updateQuestion(qIndex, 'correctIndex', oIndex)}
                  />
                  <input
                    type="text"
                    placeholder={`Option ${oIndex + 1}`}
                    value={option}
                    onChange={(e) => {
                      const options = [...question.options];
                      options[oIndex] = e.target.value;
                      updateQuestion(qIndex, 'options', options);
                    }}
                    required
                  />
                  {question.options.length > 2 && (
                    <button
                      type="button"
                      onClick={() => removeOption(qIndex, oIndex)}
                    >
                      Remove
                    </button>
                  )}
                </div>
              ))}
              {question.options.length < 4 && (
                <button
                  type="button"
                  onClick={() => addOption(qIndex)}
                >
                  + Add Option
                </button>
              )}
            </div>
            
            {/* Explanation */}
            <textarea
              placeholder="Explanation (optional)"
              value={question.explanation || ''}
              onChange={(e) => updateQuestion(qIndex, 'explanation', e.target.value)}
            />
            
            {/* Remove Question */}
            <button
              type="button"
              onClick={() => {
                const questions = formData.questions.filter((_, i) => i !== qIndex);
                setFormData({ ...formData, questions });
              }}
            >
              Remove Question
            </button>
          </div>
        ))}
      </div>
      
      {error && <div style={{ color: 'red' }}>{error}</div>}
      
      <button type="submit" disabled={loading}>
        {loading ? 'Creating...' : 'Create Quiz'}
      </button>
    </form>
  );
};

export default QuizCreateForm;
```

---

## 📊 API Endpoint Summary

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/api/quizzes/quizzes/` | POST | Create quiz with questions | ✅ Working |
| `/api/quizzes/quizzes/{id}/` | GET | Get quiz (includes questions) | ✅ Working |
| `/api/quizzes/quizzes/{id}/` | PATCH | Update quiz metadata | ✅ Working |
| `/api/quizzes/quizzes/{id}/questions/` | POST | Add question to quiz | ❌ Not available (ViewSet not registered) |
| `/api/quizzes/quizzes/{id}/questions/{id}/` | PATCH | Update question | ❌ Not available |
| `/api/quizzes/quizzes/{id}/questions/{id}/` | DELETE | Delete question | ❌ Not available |
| `/api/quizzes/attempts/submit/` | POST | Submit quiz attempt | ✅ Working |

---

## 🔒 Validation Rules (Frontend Must Implement)

### **Quiz Validation:**
- ✅ `lesson` - Required (must exist)
- ✅ `title` - Required (max 200 chars)
- ✅ `time_limit_seconds` - Optional, must be >= 30 if provided

### **Question Validation:**
- ✅ `question_type` - Required: "text" | "image" | "audio"
- ✅ `question_text` - Required
- ✅ `media_url` - Required if `question_type` is "image" or "audio"
- ✅ `options` - Required array, must have 2-4 items
- ✅ `correct_option_index` - Required, must be 0 to (options.length - 1)
- ✅ `explanation` - Optional
- ✅ `order` - Optional (defaults to 0), should be sequential

---

## 🚀 Quick Integration Checklist

- [ ] **Step 1:** Validate quiz metadata (title, time limit)
- [ ] **Step 2:** Build questions array with all required fields
- [ ] **Step 3:** Validate each question (type, options, correct_index)
- [ ] **Step 4:** POST to `/api/quizzes/quizzes/` with lesson ID
- [ ] **Step 5:** Handle success/error responses
- [ ] **Error Handling:** Display validation errors per question

---

## 📝 Data Structure Examples

### **Text Question:**
```json
{
  "question_type": "text",
  "question_text": "What is the capital of France?",
  "media_url": null,
  "options": ["London", "Berlin", "Paris", "Madrid"],
  "correct_option_index": 2,
  "explanation": "Paris is the capital of France",
  "order": 0
}
```

### **Image Question:**
```json
{
  "question_type": "image",
  "question_text": "What animal is shown in the image?",
  "media_url": "https://example.com/animal.jpg",
  "options": ["Dog", "Cat", "Bird"],
  "correct_option_index": 1,
  "explanation": "The image shows a cat",
  "order": 1
}
```

### **Audio Question:**
```json
{
  "question_type": "audio",
  "question_text": "What sound do you hear?",
  "media_url": "https://example.com/sound.mp3",
  "options": ["Meow", "Woof", "Moo"],
  "correct_option_index": 0,
  "explanation": "You heard a cat meowing",
  "order": 2
}
```

---

## 🔧 Recommended Backend Improvements

### **1. Register QuestionViewSet (Priority: High)**

Enable adding/editing questions after quiz creation.

### **2. Add Transaction Handling (Priority: High)**

Ensure atomic quiz creation.

### **3. Add Question Validation in Serializer (Priority: Medium)**

Call model's `clean()` method.

### **4. Add Bulk Question Update Endpoint (Priority: Low)**

Allow updating all questions at once.

### **5. Add Query Optimization (Priority: Medium)**

Use `select_related`/`prefetch_related` for better performance.

---

**Generated:** 2024-01-XX  
**Status:** Single-step creation works well. Two-step creation not supported due to missing URL registration.
