import requests
from app.config.settings import (OLLAMA_URL, MODEL_NAME, REQUEST_TIMEOUT,)

class LLMClient:
    """Handles communication with the LLM API."""
    def generate(self, prompt: str) -> str:
        
        url = f"{OLLAMA_URL}/api/generate"
        
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream":False,
            }
        try:
            response = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
        
            return data["response"]
        except requests.exceptions.ConnectionError:
            return "Error: Unable to connect to the LLM API. Please check the server status."
        except requests.exceptions.Timeout:
            return "Error: The request to the LLM API timed out. Please try again later."
        except Exception as e:
            return f"Error: An unexpected error occurred: {str(e)}"