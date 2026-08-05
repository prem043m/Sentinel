"""Ollama LLM client.

Handles communication with the Ollama REST API.  This is the
**only** module that knows about Ollama-specific details (URL format,
payload structure, response shape).

Implements the ``LLMService`` interface so it can be injected into
any component that requires LLM access.
"""

import requests

from app.config.settings import MODEL_NAME, OLLAMA_URL, REQUEST_TIMEOUT
from app.llm.service import LLMService


class LLMClient(LLMService):
    """Ollama-backed LLM provider.

    Sends prompts to a local Ollama instance and returns the raw
    text response.  Connection errors and timeouts are raised as
    exceptions (not silenced) so that upstream orchestration can
    decide how to handle them.
    """

    def generate(self, prompt: str) -> str:
        """Send *prompt* to Ollama and return the response text.

        Args:
            prompt: The fully-constructed prompt string.

        Returns:
            The LLM's response as a plain string.

        Raises:
            requests.exceptions.ConnectionError: Ollama is unreachable.
            requests.exceptions.Timeout: Request exceeded the timeout.
            requests.exceptions.HTTPError: Non-2xx status code.
            KeyError: Response JSON missing ``"response"`` key.
        """
        url = f"{OLLAMA_URL}/api/generate"

        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
        }

        response = requests.post(
            url, json=payload, timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        return data["response"]