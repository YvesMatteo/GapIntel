import requests

def test_revoke_youtube_analytics_access():
    base_url = "http://localhost:8000"
    endpoint_status = "/api/youtube-analytics/status"
    endpoint_disconnect = "/api/youtube-analytics/disconnect"
    headers = {}
    timeout = 30

    # Assuming API key required - set here if needed:
    # headers["X-GAP-API-Key"] = "<YOUR_API_KEY>"
    # But from PRD, the security scheme for this endpoint is ApiKeyAuth presumably header based.
    # Common pattern might be an Authorization header or custom header - since not explicit, we skip adding.

    # For the test, we need a user_id. We will create a temporary connected user_id by simulating authorize + connect flow.
    # However, no endpoint to create user or connect is exposed for test, so we assume a placeholder user_id.
    # Since instructions say if resource ID not provided, create one and delete after.
    # Here, no creation endpoint for user connection, so we just assume a dummy user_id which we will revoke access for.

    # For robustness we first check current connection status to find a user_id with connected status.
    # Since no user_id provided, we'll simulate user_id "test-user-123" for this test.

    user_id = "test-user-123"

    # Step 1: Confirm current connection status for user_id (optional)
    try:
        resp_status = requests.get(
            f"{base_url}{endpoint_status}",
            params={"user_id": user_id},
            headers=headers,
            timeout=timeout,
        )
        resp_status.raise_for_status()
        status_json = resp_status.json()
        # We expect status field "connected" or "not_connected"
        assert "status" in status_json
        assert status_json["status"] in ["connected", "not_connected"]
    except requests.RequestException as e:
        # Could not get status - continue to attempt disconnect for test purpose
        pass

    # Step 2: Call DELETE to revoke YouTube Analytics access for the user
    resp_disconnect = requests.delete(
        f"{base_url}{endpoint_disconnect}",
        params={"user_id": user_id},
        headers=headers,
        timeout=timeout,
    )

    # Validate response code 200
    assert resp_disconnect.status_code == 200

    # Validate response content - must have confirmation (description says returns confirmation)
    # As no exact schema provided, expect json or at least success indication
    try:
        resp_json = resp_disconnect.json()
        # The confirmation might be a "status" or "message" field
        # Check at least one key exists and status is success or message non-empty
        assert isinstance(resp_json, dict)
        assert ("status" in resp_json and resp_json["status"] in ["success", "disconnected", "ok"]) or ("message" in resp_json and len(str(resp_json["message"])) > 0)
    except Exception:
        # If not JSON, accept empty or text confirmation
        assert resp_disconnect.text is not None and len(resp_disconnect.text) > 0

test_revoke_youtube_analytics_access()