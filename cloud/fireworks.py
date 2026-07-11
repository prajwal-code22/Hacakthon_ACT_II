import os
from openai import OpenAI


class FireworksModel:
    def __init__(self):
        api_key = os.getenv("FIREWORKS_API_KEY")

        if not api_key:
            raise ValueError("FIREWORKS_API_KEY not found")

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.fireworks.ai/inference/v1/models",
        )

        # Change this if you want another model
        self.model = "accounts/fireworks/models/llama-v3p1-8b-instruct"

    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 512,
    ) -> str:

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful AI assistant.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return response.choices[0].message.content


fireworks_model = FireworksModel()


def initialize_model():
    return fireworks_model