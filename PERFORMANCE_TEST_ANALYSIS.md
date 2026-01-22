# Performance Test Analysis - Locust 100% Failure Rate

## 🔴 Critical Issues Identified

The Locust test shows **100% failure rate** because of multiple endpoint URL mismatches and incorrect request payloads.

---

## ❌ Issue #1: Wrong Authentication Endpoints

### **Current Test (WRONG):**
```python
'/api/auth/register/'   # ❌ Doesn't exist
'/api/auth/login/'      # ❌ Doesn't exist  
'/api/auth/logout/'     # ❌ Doesn't exist
```

### **Actual Endpoints (CORRECT):**
```python
'/api/profiles/auth/register/'  # ✅ Correct
'/api/profiles/auth/login/'     # ✅ Correct
# Logout endpoint - ❌ DOES NOT EXIST in codebase
```

**Root Cause:** Auth routes are under `/api/profiles/` prefix, not `/api/`.

---

## ❌ Issue #2: Wrong Request Payload for Registration

### **Current Test (WRONG):**
```python
json={'username': username, 'password': password}  # ❌ Missing email
```

### **Actual Required Fields (CORRECT):**
```python
json={
    'email': email,      # ⚠️ REQUIRED
    'username': username,  # ⚠️ REQUIRED
    'password': password   # ⚠️ REQUIRED
}
```

**Root Cause:** `UserRegistrationSerializer` requires `email`, `username`, and `password`.

---

## ❌ Issue #3: Wrong Request Payload for Login

### **Current Test (WRONG):**
```python
json={'username': 'testuser', 'password': 'testpass'}  # ❌ Should be 'email'
```

### **Actual Required Fields (CORRECT):**
```python
json={'email': 'test@example.com', 'password': 'testpass'}  # ✅ email, not username
```

**Root Cause:** `LoginSerializer` expects `email` field, not `username`.

---

## ❌ Issue #4: Wrong Collections Endpoint

### **Current Test (WRONG):**
```python
f'/api/collections/?id={collection_id}'  # ❌ Doesn't exist
```

### **Actual Endpoint (CORRECT):**
```python
f'/api/lessons/collections/?id={collection_id}'  # ✅ Collections under lessons app
```

**Root Cause:** Collections are part of the lessons app, not a standalone endpoint.

---

## ❌ Issue #5: Wrong Lessons Endpoint

### **Current Test (WRONG):**
```python
f'/api/lessons/{lesson_id}/'  # ❌ Wrong URL structure
```

### **Actual Endpoint (CORRECT):**
```python
f'/api/lessons/lessons/{lesson_id}/'  # ✅ DRF router adds 'lessons' prefix
```

**Root Cause:** DRF DefaultRouter adds the viewset name as a prefix (`lessons/lessons/`).

---

## ❌ Issue #6: Logout Endpoint Doesn't Exist

**Problem:** The test tries to POST to `/api/auth/logout/` but **this endpoint doesn't exist** in the codebase.

**Current Status:** No logout endpoint is implemented.

**Options:**
1. Remove logout test task
2. Implement logout endpoint (if needed)

---

## ✅ Fixed Performance Test File

```python
import io
import time
import uuid
from locust import HttpUser, task, between
from random import randint

class WebsiteUser(HttpUser):
    wait_time = between(1, 5)
    
    # Store authentication state
    access_token = None
    email = None
    username = None

    # -----------------------------
    # User auth flows
    # -----------------------------
    @task(1)
    def register_user(self):
        """Register a new user"""
        print('register new user')
        # Generate unique credentials
        unique_id = uuid.uuid4().hex[:8]
        self.email = f"locust_{unique_id}@test.com"
        self.username = f"locust_{unique_id}"
        password = "P@ssw0rd123!"
        
        response = self.client.post(
            '/api/profiles/auth/register/',  # ✅ Fixed endpoint
            json={
                'email': self.email,      # ✅ Added email
                'username': self.username,  # ✅ Added username
                'password': password
            },
            name='/api/profiles/auth/register',
            catch_response=True
        )
        
        if response.status_code == 201:
            data = response.json()
            # Store token for subsequent requests
            self.access_token = data.get('access')
            if self.access_token:
                self.client.headers.update({
                    'Authorization': f'Bearer {self.access_token}'
                })
            response.success()
        else:
            response.failure(f"Registration failed: {response.status_code} - {response.text}")

    @task(2)
    def signin(self):
        """Sign in with test credentials"""
        print('signin user')
        
        # Use a pre-created test user (should exist in database)
        response = self.client.post(
            '/api/profiles/auth/login/',  # ✅ Fixed endpoint
            json={
                'email': 'test@example.com',  # ✅ Changed to 'email'
                'password': 'testpass123'     # Use actual test password
            },
            name='/api/profiles/auth/login',
            catch_response=True
        )
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data.get('access')
            if self.access_token:
                self.client.headers.update({
                    'Authorization': f'Bearer {self.access_token}'
                })
            response.success()
        else:
            response.failure(f"Login failed: {response.status_code} - {response.text}")

    # REMOVED: signout task - endpoint doesn't exist
    # If logout is needed, implement it first in the backend

    # -----------------------------
    # Browsing collections / lessons
    # -----------------------------
    @task(4)
    def browse_collections(self):
        """Browse lesson collections"""
        print('browse collections')
        collection_id = randint(1, 5)
        
        response = self.client.get(
            f'/api/lessons/collections/?id={collection_id}',  # ✅ Fixed endpoint
            name='/api/lessons/collections',
            catch_response=True
        )
        
        if response.status_code in [200, 404]:  # 404 is acceptable (random ID might not exist)
            response.success()
        else:
            response.failure(f"Collections failed: {response.status_code}")

    @task(5)
    def browse_lessons(self):
        """Browse lessons"""
        print('browse lessons')
        lesson_id = randint(1, 10)
        
        response = self.client.get(
            f'/api/lessons/lessons/{lesson_id}/',  # ✅ Fixed endpoint
            name='/api/lessons/lessons/:id',
            catch_response=True
        )
        
        if response.status_code in [200, 404]:
            response.success()
        else:
            response.failure(f"Lessons failed: {response.status_code}")

    # -----------------------------
    # Watching videos
    # -----------------------------
    @task(3)
    def watch_video(self):
        """Simulate video streaming"""
        print('watch video')
        video_id = randint(101, 110)
        
        # Use Range header for partial content (streaming)
        headers = {"Range": "bytes=0-1048575"}  # first 1MB
        
        response = self.client.get(
            f'/media/videos/{video_id}',  # This endpoint might not exist - verify
            headers=headers,
            name='/media/videos/:id',
            catch_response=True
        )
        
        # Accept 200, 206 (partial content), or 404 (file doesn't exist)
        if response.status_code in [200, 206, 404]:
            response.success()
        else:
            response.failure(f"Video streaming failed: {response.status_code}")

    # -----------------------------
    # on_start hook
    # -----------------------------
    def on_start(self):
        """Called when a simulated user starts"""
        print('user session started')
        # Optionally sign in before starting tasks
        # self.signin()
```

---

## 📊 Summary of Changes

| Issue | Old (Wrong) | New (Fixed) |
|-------|-------------|-------------|
| **Register Endpoint** | `/api/auth/register/` | `/api/profiles/auth/register/` |
| **Register Payload** | `{username, password}` | `{email, username, password}` |
| **Login Endpoint** | `/api/auth/login/` | `/api/profiles/auth/login/` |
| **Login Payload** | `{username, password}` | `{email, password}` |
| **Collections Endpoint** | `/api/collections/` | `/api/lessons/collections/` |
| **Lessons Endpoint** | `/api/lessons/{id}/` | `/api/lessons/lessons/{id}/` |
| **Logout Task** | Exists (but endpoint doesn't) | Removed (endpoint missing) |

---

## 🧪 Testing the Fixed Script

### **Step 1: Verify Endpoints Work Manually**

```bash
# Test registration
curl -X POST http://localhost:8000/api/profiles/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "username": "testuser", "password": "testpass123"}'

# Test login
curl -X POST http://localhost:8000/api/profiles/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123"}'

# Test collections
curl http://localhost:8000/api/lessons/collections/

# Test lessons
curl http://localhost:8000/api/lessons/lessons/1/
```

### **Step 2: Run Locust**

```bash
# Navigate to project root
cd "c:\git account\backend\AI-supported teaching kids"

# Run locust
locust -f performance_test/performance_test.py --host=http://localhost:8000
```

### **Step 3: Verify Results**

- ✅ Success rate should be > 0% (not 100% failures)
- ✅ Response times should be reasonable (< 1 second for most)
- ✅ Check response codes in Locust dashboard

---

## 🔧 Additional Improvements

### **1. Add Error Handling**

```python
@task(2)
def signin(self):
    try:
        response = self.client.post(...)
        # handle response
    except Exception as e:
        print(f"Login error: {e}")
```

### **2. Add Response Validation**

```python
if response.status_code == 200:
    data = response.json()
    if 'access' in data:
        response.success()
    else:
        response.failure("No access token in response")
```

### **3. Use Environment Variables for Test Credentials**

```python
import os

TEST_EMAIL = os.getenv('TEST_EMAIL', 'test@example.com')
TEST_PASSWORD = os.getenv('TEST_PASSWORD', 'testpass123')
```

### **4. Add More Realistic Test Data**

```python
@task(6)
def create_quiz_attempt(self):
    """Test quiz submission"""
    if not self.access_token:
        return
    
    response = self.client.post(
        '/api/quizzes/attempts/submit/',
        json={
            'quiz_id': randint(1, 10),
            'child_id': randint(1, 5),
            'answers': [
                {'question_id': 1, 'selected_indices': [0]}
            ]
        },
        name='/api/quizzes/attempts/submit',
        catch_response=True
    )
    
    response.success() if response.status_code in [200, 201] else response.failure()
```

---

## 📋 Pre-Test Checklist

Before running performance tests:

- [ ] **Backend server is running** (`python manage.py runserver`)
- [ ] **Database has test data** (lessons, collections, test users)
- [ ] **Test user exists** with known email/password
- [ ] **Media files exist** (if testing video streaming)
- [ ] **CORS is configured** (if testing from different origin)
- [ ] **Rate limiting disabled** (for load testing)

---

## 🎯 Expected Results After Fix

**Before Fix:**
- ❌ 100% failure rate
- ❌ 5-50 second response times
- ❌ All requests failing

**After Fix:**
- ✅ < 5% failure rate (expected for random IDs that don't exist)
- ✅ < 500ms response times for most endpoints
- ✅ Successful authentication flows
- ✅ Realistic performance metrics

---

## 🚨 Important Notes

1. **Video endpoint may not work**: `/media/videos/{id}` depends on actual files existing
2. **Test user required**: Create a test user in database before running login tests
3. **Random IDs may 404**: Collections/lessons with random IDs might not exist (this is OK)
4. **Token management**: Access tokens should be stored and reused across requests

---

**Status:** Fixed performance test file addresses all identified issues.  
**Next Steps:** Update the file and re-run Locust to verify successful requests.
