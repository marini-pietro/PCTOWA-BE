import pytest
from flask import Flask
from typing import Generator
from flask.testing import FlaskClient
from api_server import api_app
from auth_server import auth_app

@pytest.fixture
def api_client() -> Generator[FlaskClient, None, None]:
    """
    Fixture to create a test client for the API microservice.
    """
    api_app.config["TESTING"] = True
    with api_app.test_client() as client:
        yield client

@pytest.fixture
def auth_client() -> Generator[FlaskClient, None, None]:
    """
    Fixture to create a test client for the authentication microservice.
    """
    auth_app.config["TESTING"] = True
    with api_app.test_client() as client:
        yield client