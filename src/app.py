import os
import requests

def main():
    webhook_url = os.getenv("WEBHOOK_URL")
    auth_token = os.getenv("AUTH_TOKEN")
    if not webhook_url:
        raise ValueError("Webhook URL not initialized")
    
    headers = {
        "Content-type" : "application/json",
        "Authorization" : f"Bearer {auth_token}" if auth_token else ""
    }

    payload = {
        "event" : "secure-test"
    }
    response = requests.post(webhook_url, headers= headers, json=payload)
    print(f"Status : {response.status_code}")
    print(f"Response : {response.text}")

if __name__ == "__main__":
    main()