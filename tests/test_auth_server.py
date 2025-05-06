import pytest
from flask import Flask
from flask.testing import FlaskClient
from flask_jwt_extended import create_refresh_token
from unittest.mock import patch, MagicMock
from tests.utils import auth_client
from config import STATUS_CODES

@pytest.fixture
def mock_fetchone_query():
    """
    Fixture to mock the fetchone_query function.
    """
    with patch("auth_server.fetchone_query") as mock_query:
        yield mock_query

@pytest.fixture
def mock_is_rate_limited():
    """
    Fixture to mock the is_rate_limited function.
    """
    with patch("auth_server.is_rate_limited") as mock_rate_limit:
        mock_rate_limit.return_value = False  # Default to not rate-limited
        yield mock_rate_limit

def test_health_check(auth_client: FlaskClient):
    """
    Test the health check endpoint.
    """
    response = auth_client.get("/health")
    assert response.status_code == STATUS_CODES["ok"]
    assert response.json["status"] == "ok"

def test_login_success(auth_client: FlaskClient, mock_fetchone_query):
    """
    Test successful login with valid credentials.
    """
    # Mock database response for valid credentials
    mock_fetchone_query.return_value = {
        "email_utente": "test@example.com",
        "password": "password123",
        "ruolo": "user",
    }

    response = auth_client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )

    assert response.status_code == STATUS_CODES["ok"]
    assert "access_token" in response.json
    assert "refresh_token" in response.json

def test_login_invalid_credentials(auth_client: FlaskClient, mock_fetchone_query):
    """
    Test login with invalid credentials.
    """
    # Mock database response for invalid credentials
    mock_fetchone_query.return_value = None

    response = auth_client.post(
        "/auth/login",
        json={"email": "wrong@example.com", "password": "wrongpassword"},
    )

    assert response.status_code == STATUS_CODES["unauthorized"]
    assert response.json["error"] == "Invalid credentials"

def test_login_missing_fields(auth_client: FlaskClient):
    """
    Test login with missing fields in the request body.
    """
    response = auth_client.post("/auth/login", json={"email": "test@example.com"})
    assert response.status_code == STATUS_CODES["bad_request"]
    assert response.json["error"] == "Invalid JSON payload"

def test_login_rate_limited(auth_client: FlaskClient, mock_is_rate_limited):
    """
    Test login when the auth_client is rate-limited.
    """
    # Simulate rate-limiting
    mock_is_rate_limited.return_value = True

    response = auth_client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )

    assert response.status_code == STATUS_CODES["too_many_requests"]
    assert response.json["error"] == "Rate limit exceeded"

def test_refresh_success(auth_client: FlaskClient):
    """
    Test refreshing an access token with a valid refresh token.
    """
    # Generate a valid refresh token
    refresh_token = create_refresh_token(identity="test@example.com")

    response = auth_client.post(
        "/auth/refresh",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )

    assert response.status_code == STATUS_CODES["ok"]
    assert "access_token" in response.json

def test_refresh_missing_token(auth_client: FlaskClient):
    """
    Test refreshing an access token without providing a refresh token.
    """
    response = auth_client.post("/auth/refresh")
    assert response.status_code == STATUS_CODES["unauthorized"]