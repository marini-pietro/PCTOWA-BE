import pytest
import socket
import json
from unittest.mock import patch, MagicMock
from config import (
    LOG_SERVER_PORT,
)
from log_server import (
    process_syslog_message,
    _process_message,
    process_delayed_logs,
    Logger,
    SYSLOG_PATTERN,
    delayed_logs,
    rate_limit_lock,
    RATE_LIMIT_FILE_NAME,
    RATE_LIMIT_MAX_REQUESTS,
    RATE_LIMIT_TIME_WINDOW,
)

VALID_SYSLOG_MESSAGE = "<34>1 2025-05-05T12:00:00Z host app procid msgid - Test message"
INVALID_SYSLOG_MESSAGE = "Invalid message format"
DELAYED_MESSAGE = "<34>1 2025-05-05T12:00:00Z host app procid msgid - Delayed message"
SOURCE_IP = "127.0.0.1"


@pytest.fixture
def mock_logger():
    """
    Fixture to create a mock logger for testing.
    """
    with patch("log_server.Logger") as MockLogger:
        yield MockLogger.return_value


@pytest.fixture
def mock_rate_limit_file(tmp_path):
    """
    Fixture to create a temporary rate limit file for testing.
    """
    rate_limit_file = tmp_path / "rate_limit.json"
    rate_limit_file.write_text(json.dumps({}))
    with patch("log_server.RATE_LIMIT_FILE_NAME", str(rate_limit_file)):
        yield rate_limit_file


def test_process_syslog_message_within_rate_limit(mock_logger, mock_rate_limit_file):
    """
    Test processing a syslog message within the rate limit.
    """
    message = VALID_SYSLOG_MESSAGE
    addr = (SOURCE_IP, LOG_SERVER_PORT)

    process_syslog_message(message, addr)

    # Assert that the message was processed and logged
    mock_logger.log.assert_called_once_with(
        "info",
        "2025-05-05T12:00:00Z host app procid msgid - Test message",
        "sourceIP-127.0.0.1",
    )


def test_process_syslog_message_exceeds_rate_limit(mock_logger, mock_rate_limit_file):
    """
    Test processing a syslog message that exceeds the rate limit.
    """
    message = VALID_SYSLOG_MESSAGE
    addr = (SOURCE_IP, LOG_SERVER_PORT)

    # Simulate exceeding the rate limit
    with rate_limit_lock:
        with open(mock_rate_limit_file, "w") as file:
            json.dump(
                {SOURCE_IP: {"count": RATE_LIMIT_MAX_REQUESTS + 1, "timestamp": 0}},
                file,
            )

    process_syslog_message(message, addr)

    # Assert that the message was added to the delayed logs queue
    assert len(delayed_logs) == 1
    assert delayed_logs[0] == (message, addr)

    # Assert that a warning was logged
    mock_logger.log.assert_called_once_with(
        "warning",
        f"Rate limit exceeded for 127.0.0.1. Delaying message: {message}",
        "Syslog-127.0.0.1",
    )


def test_process_invalid_syslog_message(mock_logger):
    """
    Test processing an invalid syslog message.
    """
    message = INVALID_SYSLOG_MESSAGE
    addr = (SOURCE_IP, LOG_SERVER_PORT)

    _process_message(message, addr)

    # Assert that a warning was logged for the invalid message
    mock_logger.log.assert_called_once_with(
        "warning", f"Invalid syslog message: {message}", "Syslog-127.0.0.1"
    )


def test_process_delayed_logs(mock_logger):
    """
    Test processing delayed logs from the queue.
    """
    message = DELAYED_MESSAGE
    addr = (SOURCE_IP, LOG_SERVER_PORT)

    # Add a delayed log to the queue
    delayed_logs.append((message, addr))

    # Process the delayed logs
    process_delayed_logs()

    # Assert that the delayed log was processed and logged
    mock_logger.log.assert_called_once_with(
        "info",
        "2025-05-05T12:00:00Z host app procid msgid - Delayed message",
        "sourceIP-127.0.0.1",
    )


def test_syslog_pattern_matching():
    """
    Test the regex pattern for matching syslog messages.
    """
    message = VALID_SYSLOG_MESSAGE
    match = SYSLOG_PATTERN.match(message)

    # Assert that the message matches the pattern and fields are extracted correctly
    assert match is not None
    assert match.group(1) == "34"  # PRI
    assert match.group(2) == "1"  # VERSION
    assert match.group(3) == "2025-05-05T12:00:00Z"  # TIMESTAMP
    assert match.group(4) == "host"  # HOSTNAME
    assert match.group(5) == "app"  # APP-NAME
    assert match.group(6) == "procid"  # PROCID
    assert match.group(7) == "msgid"  # MSGID
    assert match.group(9) == "Test message"  # MSG
