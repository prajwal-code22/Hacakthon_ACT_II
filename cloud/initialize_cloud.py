import os
import requests


class FireworksModel:

    def __init__(self):
        self.api_key = os.getenv("FIREWORKS_API_KEY")

        if not self.api_key:
            raise ValueError("FIREWORKS_API_KEY not found.")

        self.url = "https://api.fireworks.ai/inference/v1/chat/completions"

        self.model = "accounts/fireworks/models/llama-v3p1-8b-instruct"

    def generate(self, prompt, temperature=0.7, max_tokens=512):

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        response = requests.post(
            self.url,
            headers=headers,
            json=payload,
            timeout=120,
        )

        print(response.status_code)
        print(response.text)

        response.raise_for_status()

        return response.json()["choices"][0]["message"]["content"]