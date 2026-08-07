import logging
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "sentinel.log"


class StructuredFormatter(logging.Formatter):
    """Custom logging formatter to inject request correlation ID and component."""

    def format(self, record: logging.LogRecord) -> str:
        if not hasattr(record, "request_id"):
            from app.core.request_context import get_request_id
            record.request_id = get_request_id()
        if not hasattr(record, "component"):
            record.component = record.name
        return super().format(record)


def setup_logger() -> logging.Logger:
    """Setup root and file loggers with StructuredFormatter."""
    formatter = StructuredFormatter(
        "%(asctime)s | %(levelname)s | [%(request_id)s] [%(component)s] | %(message)s"
    )

    root = logging.getLogger()
    # Set level on root so handlers receive all records
    root.setLevel(logging.INFO)

    # Avoid duplicating handlers if setup_logger is called multiple times
    if not root.handlers:
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setFormatter(formatter)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        root.addHandler(file_handler)
        root.addHandler(stream_handler)

    return logging.getLogger("SentinelAI")