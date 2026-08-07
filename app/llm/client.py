"""Ollama LLM client with detailed HTTP and generation latency metrics.

Handles communication with the Ollama REST API, recording connection setup,
waiting/response headers latency, reading content data stream, and JSON parsing.
"""

from __future__ import annotations

import json
import time
import requests

from app.config.settings import MODEL_NAME, OLLAMA_URL, REQUEST_TIMEOUT
from app.core.logger import RequestLogger
from app.core.timing import record_timing
from app.llm.service import LLMService

logger = RequestLogger("SentinelAI.LLMClient")


class LLMClient(LLMService):
    """Ollama-backed LLM provider with instrumentation.

    Sends prompts to a local Ollama instance and returns the raw response text,
    measuring connection and streaming latencies.
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

        logger.info("Sending prompt to Ollama model '%s' (%d chars)...", MODEL_NAME, len(prompt))

        start_post = time.perf_counter()

        # Measure headers/waiting vs stream content reading
        response = requests.post(
            url, json=payload, timeout=REQUEST_TIMEOUT, stream=True
        )
        headers_received = time.perf_counter()
        
        response.raise_for_status()
        
        content = response.content
        stream_completed = time.perf_counter()

        data = json.loads(content)
        json_parsed = time.perf_counter()

        # Calculate metrics
        post_time_ms = (headers_received - start_post) * 1000.0
        stream_time_ms = (stream_completed - headers_received) * 1000.0
        json_time_ms = (json_parsed - stream_completed) * 1000.0
        total_time_ms = (json_parsed - start_post) * 1000.0

        # Record timing metrics
        record_timing("llm_post_waiting", post_time_ms)
        record_timing("llm_stream_reading", stream_time_ms)
        record_timing("llm_json_parsing", json_time_ms)
        record_timing("llm_request", total_time_ms)

        logger.info(
            "Ollama Request Timing: POST/Headers=%.1f ms, Streaming/Read=%.1f ms, JSON=%.1f ms, Total=%.1f ms",
            post_time_ms,
            stream_time_ms,
            json_time_ms,
            total_time_ms,
        )

        return data["response"]

    def warm_up(self) -> dict[str, Any]:
        """Check connection to Ollama, retrieve model status, and trigger model warming.

        Returns:
            A dictionary containing status, loaded, warm, details.
        """
        url_tags = f"{OLLAMA_URL}/api/tags"
        url_show = f"{OLLAMA_URL}/api/show"
        url_generate = f"{OLLAMA_URL}/api/generate"

        status = {
            "connected": False,
            "model_installed": False,
            "warm": False,
            "details": {}
        }

        try:
            # 1. Check connection and list models
            res_tags = requests.get(url_tags, timeout=5)
            if res_tags.status_code == 200:
                status["connected"] = True
                models = [m["name"] for m in res_tags.json().get("models", [])]
                # Match name exactly or by prefix/tagless name
                model_base = MODEL_NAME.split(":")[0]
                if MODEL_NAME in models or any(model_base in m for m in models):
                    status["model_installed"] = True
            
            # 2. Get model details
            if status["model_installed"]:
                res_show = requests.post(url_show, json={"name": MODEL_NAME}, timeout=5)
                if res_show.status_code == 200:
                    status["details"] = res_show.json()
            
            # 3. Warm/load the model (triggering initial load latency)
            logger.info("Warming up Ollama model '%s' (this may take a few seconds)...", MODEL_NAME)
            start_time = time.perf_counter()
            res_gen = requests.post(
                url_generate,
                json={"model": MODEL_NAME, "prompt": "", "keep_alive": "10m"},
                timeout=REQUEST_TIMEOUT
            )
            elapsed = time.perf_counter() - start_time
            if res_gen.status_code == 200:
                status["warm"] = True
                logger.info("Ollama model '%s' warmed successfully in %.2f seconds.", MODEL_NAME, elapsed)
            else:
                logger.warning("Ollama model warming request returned status: %d", res_gen.status_code)

        except Exception as e:
            logger.error("Failed to connect/warm Ollama model: %s", e)

        return status