import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_handle_stripe_subscription_webhook():
    url = f"{BASE_URL}/webhook/stripe-subscription"
    # Example Stripe webhook event payload (minimal required fields for testing)
    payload = {
        "id": "evt_test_webhook",
        "object": "event",
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": "sub_test_subscription",
                "object": "subscription",
                "status": "active",
                "customer": "cus_test_customer"
            }
        }
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request to {url} failed: {e}"

    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"

test_handle_stripe_subscription_webhook()