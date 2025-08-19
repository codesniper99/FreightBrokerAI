import os
import requests
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def main():

    webhook_url = os.getenv("WEBHOOK_URL")
    auth_token = os.getenv("AUTH_TOKEN")
    api_key = os.getenv("API_KEY")
    if not webhook_url:
        raise ValueError("Webhook URL not initialized")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}" if auth_token else "",
        "x-api-key" : f"{api_key}" if api_key else ""
    }

    payload = {
                    "message": "I want a new load of 5kg",
                    "event": "test"
               }
    response = requests.post(url=webhook_url, headers=headers, json=payload)
    print(f"Status : {response.status_code}")
    print(f"Response : {response.text}")


if __name__ == "__main__":
    main()
