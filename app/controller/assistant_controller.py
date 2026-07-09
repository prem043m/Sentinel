from app.llm.client import LLMClient


class AssistantController:
    """Coordinates the application's workflow."""

    def __init__(self, llm):
        self.llm = llm

    def process_message(self, message: str) -> str:
        return self.llm.generate(message)