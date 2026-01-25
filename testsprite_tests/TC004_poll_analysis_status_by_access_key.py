import requests
import time
import uuid

BASE_URL = "http://localhost:8000"
API_KEY = "test-api-key-123456"  # Replace with valid API key if required

HEADERS_AUTH = {
    "X-GAP-API-Key": API_KEY
}

def test_poll_analysis_status_by_access_key():
    """
    Test the /status/{access_key} GET endpoint to verify it returns the correct analysis status
    including queued, processing, completed, or failed states.
    """
    # Generate a unique access_key for testing
    unique_access_key = f"GAP-{uuid.uuid4().hex[:12].upper()}"

    # First, create a new analysis to get a valid access_key
    analyze_url = f"{BASE_URL}/analyze"
    analyze_payload = {
        "channel_name": "TestChannel1234",
        "access_key": unique_access_key,
        "email": "testuser@example.com"
    }
    headers = {
        "Content-Type": "application/json",
        # Assume API key required in header 'X-GAP-API-Key' for /analyze endpoint:
        "X-GAP-API-Key": API_KEY
    }

    try:
        # Trigger gap analysis to generate a new analysis job with an access key
        resp = requests.post(analyze_url, json=analyze_payload, headers=headers, timeout=30)
        assert resp.status_code == 200, f"Analyze POST failed with status code {resp.status_code}"
        resp_json = resp.json()
        assert "access_key" in resp_json, "Response missing access_key"
        access_key = resp_json["access_key"]

        # Poll the /status/{access_key} endpoint to get analysis status
        status_url = f"{BASE_URL}/status/{access_key}"
        # Poll multiple times to cover different states: queued, processing, completed, or failed
        valid_statuses = {"queued", "processing", "completed", "failed"}
        last_status = None
        for _ in range(5):
            status_resp = requests.get(status_url, timeout=30)  # No auth headers as per PRD
            assert status_resp.status_code == 200, f"Status GET failed with status code {status_resp.status_code}"
            status_json = status_resp.json()

            # Validate mandatory fields
            assert "access_key" in status_json, "Response missing access_key"
            assert "channel_name" in status_json, "Response missing channel_name"
            assert "status" in status_json, "Response missing status"
            assert status_json["access_key"] == access_key, "Mismatched access_key"
            assert status_json["channel_name"] == analyze_payload["channel_name"], "Mismatched channel_name"
            assert status_json["status"] in valid_statuses, f"Invalid status value: {status_json['status']}"

            # Validate datetime fields if present
            for dt_field in ("created_at", "completed_at"):
                if dt_field in status_json and status_json[dt_field] is not None:
                    # Basic check for ISO 8601 datetime format
                    assert isinstance(status_json[dt_field], str) and len(status_json[dt_field]) > 0

            last_status = status_json["status"]
            if last_status in {"completed", "failed"}:
                break  # Stop polling if final state reached
            time.sleep(1)
    finally:
        # There's no specific delete endpoint to clean analysis by access_key,
        # so no resource cleanup is performed here.
        pass

test_poll_analysis_status_by_access_key()
