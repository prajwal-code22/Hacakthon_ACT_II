"""
gemma.py
---------
Gemma local LLM service via Ollama.

Prerequisites
-------------
1. Install Ollama: https://ollama.com/download
2. Pull the model:
       ollama pull gemma3
3. Start Ollama (it runs as a background service automatically on most systems):
       ollama serve
"""

import logging

import requests

logger = logging.getLogger(__name__)


class Gemma:
    """
    Thin wrapper around Ollama's REST API for local Gemma inference.

    Endpoint : http://localhost:11434/api/generate
    Model    : gemma3
    """

    ENDPOINT = "http://localhost:11434/api/generate"
    MODEL    = "gemma3"
    TIMEOUT  = 180  # seconds

    def generate(self, query: str) -> str:
        """
        Send *query* to local Gemma via Ollama and return the response text.

        Falls back to a descriptive error message if Ollama is offline or
        the model is not available — so the API never crashes.
        """
        try:
            payload = {
                "model":  self.MODEL,
                "prompt": query,
                "stream": False,
            }
            logger.info("Calling Gemma (LOCAL) → %s…", query[:80])
            response = requests.post(self.ENDPOINT, json=payload, timeout=self.TIMEOUT)
            response.raise_for_status()

            text = response.json().get("response", "").strip()
            logger.info("Gemma responded (%d chars)", len(text))
            return text or "Gemma returned an empty response."

        except requests.exceptions.ConnectionError:
            msg = (
                "⚠️  **Ollama is not running.**\n\n"
                "Start it with the following commands:\n"
                "```\nollama serve\nollama pull gemma3\n```"
            )
            logger.warning("Ollama connection refused at %s", self.ENDPOINT)
            return msg

        except requests.exceptions.Timeout:
            msg = (
                f"⚠️  **Gemma timed out** after {self.TIMEOUT} s.\n"
                "Your query may be too long for local inference. Try a shorter prompt."
            )
            logger.warning("Gemma request timed out")
            return msg

        except requests.exceptions.HTTPError as exc:
            msg = f"⚠️  **Ollama HTTP error:** {exc}"
            logger.error(msg)
            return msg

        except Exception as exc:  # noqa: BLE001
            msg = f"⚠️  **Gemma error:** {exc}"
            logger.error(msg)
            return msg
