import requests

def test_get_real_time_job_queue_metrics():
    base_url = "http://localhost:8000"
    url = f"{base_url}/queue-status"
    timeout = 30

    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as e:
        assert False, f"Request to /queue-status failed: {e}"

    # Validate response code and content type
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    try:
        json_data = response.json()
    except ValueError:
        assert False, "Response is not valid JSON"

    # Validate required fields in response
    for field in ["queue_length", "active_jobs", "max_concurrent"]:
        assert field in json_data, f"Missing field '{field}' in response"
        assert isinstance(json_data[field], int), f"Field '{field}' should be integer, got {type(json_data[field])}"

    # Validate non-negative values (queue length and active jobs shouldn't be negative)
    assert json_data["queue_length"] >= 0, "queue_length should be non-negative"
    assert json_data["active_jobs"] >= 0, "active_jobs should be non-negative"
    assert json_data["max_concurrent"] >= 0, "max_concurrent should be non-negative"

test_get_real_time_job_queue_metrics()