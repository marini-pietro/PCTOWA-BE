import pytest
from flask import Flask
from flask.testing import FlaskClient
from flask_jwt_extended import create_access_token, create_refresh_token
from typing import Generator
from api_server import main_api
from auth_server import auth_api
from api_blueprints.user_bp import user_bp
from api_blueprints.sector_bp import sector_bp
from api_blueprints.legalform_bp import legalform_bp

@pytest.fixture
def api_client() -> Generator[FlaskClient, None, None]:
    """
    Fixture to create a test client for the API microservice.
    """
    main_api.config["TESTING"] = True
    with main_api.test_client() as client:
        yield client

@pytest.fixture
def auth_client() -> Generator[FlaskClient, None, None]:
    """
    Fixture to create a test client for the authentication microservice.
    """
    auth_api.config["TESTING"] = True
    with auth_api.test_client() as client:
        yield client

@pytest.fixture
def user_client() -> Generator[FlaskClient, None, None]:
    """
    Fixture to create a test client for the user blueprint.
    """
    app = Flask(__name__)
    app.register_blueprint(user_bp, url_prefix='/user')
    app.config['JWT_SECRET_KEY'] = 'test_secret'
    with app.test_client() as client:
        yield client

@pytest.fixture
def sector_client() -> Generator[FlaskClient, None, None]:
    """
    Fixture to create a test client for the sector blueprint.
    """
    app = Flask(__name__)
    app.register_blueprint(sector_bp, url_prefix='/sector')
    app.config['JWT_SECRET_KEY'] = 'test_secret'
    with app.test_client() as client:
        yield client

@pytest.fixture
def legalform_client() -> Generator[FlaskClient, None, None]:
    """
    Fixture to create a test client for the legalform blueprint.
    """
    app = Flask(__name__)
    app.register_blueprint(legalform_bp, url_prefix='/legalform')
    app.config['JWT_SECRET_KEY'] = 'test_secret'
    with app.test_client() as client:
        yield client

@pytest.fixture
def admin_token() -> str:
    """
    Fixture to create an admin JWT token.
    """
    return create_access_token(identity={"role": "admin"})

@pytest.fixture
def refresh_token() -> str:
    """
    Fixture to create a refresh token.
    """
    return create_refresh_token(identity="test@example.com")