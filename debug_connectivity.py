import requests

# import sys

BASE_URL = "http://127.0.0.1:8000"


def test_endpoint(method, path, data=None):
    url = f"{BASE_URL}{path}"
    print(f"Testing {method} {url}...", end=" ")
    try:
        if method == "GET":
            resp = requests.get(url)
        else:
            resp = requests.post(url, json=data)

        print(f"Status: {resp.status_code}")
        if resp.status_code >= 400:
            print(f"  Response: {resp.text[:200]}")
    except requests.exceptions.ConnectionError:
        print("FAILED: Connection Refused. Is the server running?")
        return False
    except Exception as e:
        print(f"FAILED: {e}")
        return False
    return True


print("--- DIAGNOSTIC START ---")
# 1. Test Register
test_endpoint(
    "POST",
    "/api/profiles/auth/register/",
    {
        "username": "debug_user_001",
        "email": "debug001@test.com",
        "password": "Password123!",
    },
)
# 2. Test Collections
test_endpoint("GET", "/api/lessons/collections/")
# 3. Test Lessons
test_endpoint("GET", "/api/lessons/lessons/")
print("--- DIAGNOSTIC END ---")
