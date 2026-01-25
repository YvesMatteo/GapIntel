import requests

def test_initiate_youtube_analytics_oauth_flow():
    base_url = "http://localhost:8000"
    endpoint = "/api/youtube-analytics/authorize"
    api_key = "valid_api_key_example"  # Replace with a valid API key for the test
    user_id = "test_user_123"  # Example user_id for test

    headers = {
        "X-GAP-API-Key": api_key
    }
    params = {
        "user_id": user_id
    }

    try:
        response = requests.get(
            f"{base_url}{endpoint}",
            headers=headers,
            params=params,
            timeout=30
        )
    except requests.RequestException as e:
        assert False, f"HTTP request failed: {e}"

    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    try:
        json_data = response.json()
    except ValueError:
        assert False, "Response is not valid JSON"

    assert "status" in json_data, "'status' field missing in response JSON"
    assert json_data["status"] == "success" or json_data["status"] == "ok" or isinstance(json_data["status"], str), "Status field unexpected value"
    assert "authorization_url" in json_data, "'authorization_url' field missing in response JSON"
    assert isinstance(json_data["authorization_url"], str) and json_data["authorization_url"].startswith("http"), "authorization_url is not a valid URL string"
    assert "state" in json_data, "'state' field missing in response JSON"
    assert isinstance(json_data["state"], str) and len(json_data["state"]) > 0, "state field is empty or not a string"

test_initiate_youtube_analytics_oauth_flow()