import logging
import random
import uuid
from locust import HttpUser, task, between


class ImprovedWebsiteUser(HttpUser):
    wait_time = between(1, 5)

    # Local cache for valid IDs to avoid 404s
    collection_ids = []
    lesson_ids = []

    auth_token = None

    def on_start(self):
        """
        Executed once per user at startup.
        1. Register a unique user.
        2. Login to get token.
        3. Discover valid content IDs.
        """
        self.username = f"locust_{uuid.uuid4().hex[:8]}"
        self.email = f"{self.username}@loadtest.com"
        self.password = "TestPass123!"

        # 1. Register
        with self.client.post(
            "/api/profiles/auth/register/",
            json={
                "username": self.username,
                "email": self.email,
                "password": self.password,
            },
            catch_response=True,
        ) as response:
            if response.status_code != 201:
                logging.error(f"Registration failed: {response.text}")
                return

        # 2. Login
        with self.client.post(
            "/api/profiles/auth/login/",
            json={"email": self.email, "password": self.password},
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access")
                self.client.headers.update(
                    {"Authorization": f"Bearer {self.auth_token}"}
                )
            else:
                logging.error(f"Login failed: {response.text}")

        # 3. Discover Content (Populate cache)
        self._refresh_content_cache()

        # 4. Create a child profile (needed for progress tracking)
        self.child_id = None
        if self.auth_token:
            with self.client.post(
                "/api/profiles/children/",
                json={"nickname": f"Kid_{self.username}", "age": 5},
                catch_response=True,
            ) as response:
                if response.status_code == 201:
                    self.child_id = response.json().get("id")

    def _refresh_content_cache(self):
        """Fetch valid IDs from the API."""
        # Collections
        with self.client.get("/api/lessons/collections/", catch_response=True) as resp:
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                self.collection_ids = [item["id"] for item in results]

        # Lessons
        with self.client.get("/api/lessons/lessons/", catch_response=True) as resp:
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                self.lesson_ids = [item["id"] for item in results]

    @task(3)
    def browse_lessons(self):
        """Browse lesson list."""
        self.client.get("/api/lessons/lessons/", name="/api/lessons/lessons/")

    @task(5)
    def view_lesson_detail(self):
        """View a specific lesson."""
        if not self.lesson_ids:
            self._refresh_content_cache()
            if not self.lesson_ids:
                return

        lesson_id = random.choice(self.lesson_ids)
        self.client.get(
            f"/api/lessons/lessons/{lesson_id}/", name="/api/lessons/lessons/:id"
        )

    @task(2)
    def track_progress(self):
        """Simulate finishing a lesson."""
        if not self.lesson_ids or not self.child_id:
            return

        lesson_id = random.choice(self.lesson_ids)

        # Simulate watching
        self.client.post(
            f"/api/lessons/lessons/{lesson_id}/track-progress/",
            json={
                "child_id": self.child_id,
                "completion_status": True,
                "time_spent": random.randint(60, 300),
                "video_watch_percentage": random.randint(50, 100),
                "number_of_clicks": random.randint(1, 10),
            },
            name="/api/lessons/lessons/:id/track-progress",
        )

    @task(1)
    def watch_video_stream(self):
        """Simulate video streaming with Range headers."""
        # Note: This checks for videos in general.
        # In a real test, we'd grab the 'video_url' from the lesson detail.
        # For now, we'll try a generic media path if we assume IDs match,
        # but better to skip if we don't have exact URLs.
        pass
