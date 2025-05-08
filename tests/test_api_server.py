import pytest
import time
from flask import Flask
from flask.testing import FlaskClient
from tests.utils import api_client
from config import RATE_LIMIT_MAX_REQUESTS, URL_PREFIX, STATUS_CODES, RATE_LIMIT_TIME_WINDOW

# Test the health endpoint in api_server.py
def test_health_check(api_client: FlaskClient):
    """
    Test the health check endpoint.
    """
    response = api_client.get("/health")
    assert response.status_code == STATUS_CODES["ok"]
    assert response.json["status"] == "ok"

# Test the rate limiting in api_server.py
def test_rate_limit(client: FlaskClient):
    """
    Test the rate limiting functionality.
    """
    # Simulate multiple requests from the same client IP
    for _ in range(RATE_LIMIT_MAX_REQUESTS):
        response = client.get(f"{URL_PREFIX}health")
        assert response.status_code == STATUS_CODES["ok"]

    # Wait for the rate limit window to reset before sending another request
    time.sleep(RATE_LIMIT_TIME_WINDOW + 1) 
    response = client.get(f"{URL_PREFIX}health")
    assert response.status_code == STATUS_CODES["ok"]
    assert response.json["status"] == "ok"

    # Simulate multiple requests from the same client IP
    time.sleep(RATE_LIMIT_TIME_WINDOW + 1)  # Wait for the rate limit window to reset
    for _ in range(RATE_LIMIT_MAX_REQUESTS):
        response = client.get(f"{URL_PREFIX}health")
        assert response.status_code == STATUS_CODES["ok"]

    # Simulate the request that exceeds the rate limit
    response = client.get(f"{URL_PREFIX}health")
    assert response.status_code == STATUS_CODES["too_many_requests"]
    assert response.json["error"] == "Rate limit exceeded"

def test_health_check_unauthorized(client: FlaskClient):
    """
    Test the health check endpoint without proper authorization.
    """
    response = client.get("/health")
    assert response.status_code == STATUS_CODES["unauthorized"]
    assert "error" in response.json

def test_invalid_configuration(client: FlaskClient, mocker):
    """
    Test the server behavior with an invalid configuration.
    """
    mocker.patch("config.JWT_SECRET_KEY", None)  # Simulate missing JWT secret key
    response = client.get("/health")
    assert response.status_code == STATUS_CODES["internal_server_error"]
    assert "error" in response.json




