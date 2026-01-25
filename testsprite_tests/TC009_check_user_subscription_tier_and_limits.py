import requests

BASE_URL = "http://localhost:8000"
API_KEY = "your-valid-api-key"  # Replace with a valid API key
TEST_EMAIL = "testuser@example.com"  # Replace with a valid test user email

def test_check_user_subscription_tier_and_limits():
    url = f"{BASE_URL}/subscription/status"
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    params = {
        "email": TEST_EMAIL
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
    except requests.RequestException as e:
        assert False, f"Request to /subscription/status failed: {e}"

    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"

    try:
        data = response.json()
    except ValueError:
        assert False, "Response body is not valid JSON"

    assert isinstance(data, dict), "Response JSON is not an object"

    # Validate required fields in response
    assert "tier" in data, "Response JSON missing 'tier'"
    assert isinstance(data["tier"], str), "'tier' should be a string"

    assert "status" in data, "Response JSON missing 'status'"
    assert isinstance(data["status"], str), "'status' should be a string"

    assert "analyses_remaining" in data, "Response JSON missing 'analyses_remaining'"
    assert isinstance(data["analyses_remaining"], int), "'analyses_remaining' should be an integer"

    # Removed strict checking of tier and status values as not explicitly defined in PRD

test_check_user_subscription_tier_and_limits()
