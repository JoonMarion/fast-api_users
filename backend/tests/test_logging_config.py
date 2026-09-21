import json
import logging
from io import StringIO

from app.logging_config import configure_logging


def test_configure_logging_outputs_structured_json() -> None:
    application_logger = logging.getLogger("app")
    previous_handlers = application_logger.handlers.copy()
    previous_level = application_logger.level
    previous_propagate = application_logger.propagate
    stream = StringIO()

    try:
        configure_logging(stream=stream)
        logger = logging.getLogger("app.test")
        logger.info(
            "User fetch completed",
            extra={
                "event": "users_fetch_completed",
                "requested_count": 3,
                "succeeded_count": 2,
                "failed_count": 1,
            },
        )
    finally:
        application_logger.handlers = previous_handlers
        application_logger.setLevel(previous_level)
        application_logger.propagate = previous_propagate

    payload = json.loads(stream.getvalue())
    assert payload["level"] == "INFO"
    assert payload["logger"] == "app.test"
    assert payload["message"] == "User fetch completed"
    assert payload["event"] == "users_fetch_completed"
    assert payload["requested_count"] == 3
    assert payload["succeeded_count"] == 2
    assert payload["failed_count"] == 1
    assert "timestamp" in payload
