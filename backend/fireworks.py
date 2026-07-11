import os
import requests
from dotenv import load_dotenv

load_dotenv()

class Fireworks:

    URL = "https://api.fireworks.ai/inference/v1/chat/completions"

    MODEL = "accounts/fireworks/models/gpt-oss-120b"

    def __init__(self):
        self.api_key = os.getenv("FIREWORKS_API_KEY")

    def generate(self, prompt):

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 512,
        }

        response = requests.post(
            self.URL,
            headers=headers,
            json=payload,
            timeout=120,
        )

        print(response.status_code)
        print(response.text)

        response.raise_for_status()

        return response.json()["choices"][0]["message"]["content"]