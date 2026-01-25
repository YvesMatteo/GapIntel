import requests

def test_check_youtube_analytics_connection_status():
    base_url = "http://localhost:8000"
    endpoint = "/api/youtube-analytics/status"
    user_id = "test-user-123"  # Replace with a valid user_id for a real test
    api_key = "test-api-key"   # Replace with a valid API key if required
    
    headers = {
        "ApiKeyAuth": api_key
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
        response.raise_for_status()
    except requests.RequestException as e:
        assert False, f"Request failed: {e}"
    
    json_response = response.json()

    assert "status" in json_response, "Response missing 'status'"
    assert json_response["status"] in ("connected", "not_connected"), f"Unexpected status value: {json_response['status']}"

    # For connected status, channel_id and expires_at must be present and valid
    if json_response["status"] == "connected":
        assert "channel_id" in json_response and isinstance(json_response["channel_id"], str) and json_response["channel_id"], "Missing or invalid channel_id for connected status"
        assert "expires_at" in json_response and isinstance(json_response["expires_at"], str) and json_response["expires_at"], "Missing or invalid expires_at for connected status"

    # For not_connected status, channel_id and expires_at may be absent, so no assertion needed

test_check_youtube_analytics_connection_status()