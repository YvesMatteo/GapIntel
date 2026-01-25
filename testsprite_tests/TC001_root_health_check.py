import requests

def test_root_health_check():
    base_url = "http://localhost:8000"
    url = f"{base_url}/"
    try:
        response = requests.get(url, timeout=30)
    except requests.RequestException as e:
        assert False, f"Request to {url} failed: {e}"
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    try:
        data = response.json()
    except ValueError:
        assert False, "Response is not valid JSON"
    assert isinstance(data, dict), "Response JSON is not an object"
    assert "status" in data and isinstance(data["status"], str), "'status' field missing or not a string"
    assert "service" in data and isinstance(data["service"], str), "'service' field missing or not a string"
    assert "version" in data and isinstance(data["version"], str), "'version' field missing or not a string"

test_root_health_check()