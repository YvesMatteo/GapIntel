import requests

def test_trigger_gap_analysis_for_youtube_channel():
    base_url = "http://localhost:8000"
    endpoint = f"{base_url}/analyze"
    api_key = "valid_api_key_example"  # Replace with a valid API key string in 'ApiKeyAuth' header
    headers = {
        "Content-Type": "application/json",
        "ApiKeyAuth": api_key
    }
    payload = {
        "channel_name": "@examplechannel",
        "access_key": "GAP-12345ABCDE",
        "email": "user@example.com",
        "video_count": 5,
        "include_shorts": True,
        "tier": "pro",
        "language": "en"
    }

    try:
        response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
    except requests.RequestException as e:
        assert False, f"Request to /analyze endpoint failed: {e}"

    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"

    try:
        resp_json = response.json()
    except ValueError:
        assert False, "Response is not valid JSON"

    # Validate expected properties in response
    assert "status" in resp_json, "'status' not in response"
    assert resp_json["status"] == "queued" or resp_json["status"] == "processing" or resp_json["status"] == "completed", \
        f"Unexpected status value: {resp_json['status']}"

    assert "message" in resp_json and isinstance(resp_json["message"], str), "'message' missing or not a string"
    assert "access_key" in resp_json and isinstance(resp_json["access_key"], str), "'access_key' missing or not a string"
    assert "queue_position" in resp_json and isinstance(resp_json["queue_position"], int), "'queue_position' missing or not an integer"

test_trigger_gap_analysis_for_youtube_channel()