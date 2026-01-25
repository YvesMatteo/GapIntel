import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_railway_health_check():
    url = f"{BASE_URL}/health"
    try:
        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as e:
        assert False, f"Request to {url} failed: {e}"

    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"

    try:
        data = response.json()
    except ValueError:
        assert False, "Response is not valid JSON"

    assert isinstance(data, dict), "Response JSON is not an object"
    assert "status" in data, "'status' field missing in response"
    assert "service" in data, "'service' field missing in response"
    assert isinstance(data["status"], str), "'status' field is not a string"
    assert isinstance(data["service"], str), "'service' field is not a string"
    assert data["status"].lower() in ["ok", "healthy", "running", "up", "active", "healthy"], \
        f"Unexpected status value: {data['status']}"
    assert len(data["service"]) > 0, "'service' field is empty"

test_railway_health_check()