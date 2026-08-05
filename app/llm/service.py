"""Abstract interface for LLM services.

This module defines the contract that every LLM provider must
implement.  ``LLMPlanner`` depends on this interface — never on a
concrete client — so providers can be swapped without touching the
planning layer.

Current providers:
- ``LLMClient`` (Ollama, in ``app/llm/client.py``)

Future providers (not yet implemented):
- OpenAI
- Google Gemini
- Anthropic Claude
- Local GGUF
- Mock / test harness
"""

from abc import ABC, abstractmethod


class LLMService(ABC):
    """Base interface for every LLM provider.

    Implementations must convert a prompt string into a response
    string.  They may raise any exception on failure (connection
    errors, timeouts, API errors).  Callers (e.g. ``LLMPlanner``)
    are expected to let exceptions propagate; the
    ``PlannerOrchestrator`` handles fallback.
    """

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Send *prompt* to the LLM and return the raw text response.

        Args:
            prompt: The fully-constructed prompt string.

        Returns:
            The LLM's response as a plain string.

        Raises:
            Any exception if the LLM call fails.
        """
        raise NotImplementedError
