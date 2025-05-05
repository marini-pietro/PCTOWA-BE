import pytest
from flask import Flask
from typing import Generator
from flask.testing import FlaskClient
from auth_server import app

# User login related tests
def test_login_success(client: FlaskClient):
    """
    Test successful login with valid credentials.
    """
    response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json
    assert "refresh_token" in response.json

def test_login_invalid_credentials(client: FlaskClient):
    """
    Test login with invalid credentials.
    """
    response = client.post(
        "/auth/login",
        json={"email": "wrong@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert response.json["error"] == "Invalid credentials"

def test_login_missing_fields(client: FlaskClient):
    """
    Test login with missing fields in the request body.
    """
    response = client.post("/auth/login", json={"email": "test@example.com"})
    assert response.status_code == 400
    assert response.json["error"] == "missing email or password"