import json
import logging
from datetime import UTC, datetime
from typing import TextIO

STRUCTURED_FIELDS = (
    "event",
    "user_id",
    "attempt",
    "max_attempts",
    "delay_seconds",
    "retry_reason",
    "retry_after_used",
    "status_code",
    "requested_count",
    "succeeded_count",
    "failed_count",
    "max_concurrency",
)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(
                timespec="milliseconds"
            ),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for field in STRUCTURED_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value

        if record.exc_info is not None:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def configure_logging(
    *, level: int = logging.INFO, stream: TextIO | None = None
) -> None:
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())

    application_logger = logging.getLogger("app")
    application_logger.handlers.clear()
    application_logger.addHandler(handler)
    application_logger.setLevel(level)
    application_logger.propagate = False
