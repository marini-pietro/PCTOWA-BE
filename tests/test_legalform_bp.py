import pytest
from flask import Flask
from flask_jwt_extended import create_access_token
from api_blueprints.legalform_bp import legalform_bp


@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(legalform_bp, url_prefix="/legalform")
    app.config["JWT_SECRET_KEY"] = "test_secret"
    with app.test_client() as client:
        yield client


def test_post_legalform(legalform_client, mocker, admin_token):
    mocker.patch("api_blueprints.legalform_bp.execute_query", return_value=1)
    response = legalform_client.post(
        "/legalform",
        json={"forma_giuridica": "SRL"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    assert response.json["outcome"] == "legal form successfully created"


def test_get_legalforms(client, mocker):
    mocker.patch(
        "api_blueprints.legalform_bp.fetchall_query",
        return_value=[{"forma_giuridica": "SRL"}],
    )
    token = create_access_token(identity={"role": "admin"})
    response = client.get("/legalform", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json[0]["forma_giuridica"] == "SRL"


def test_delete_legalform(client, mocker):
    mocker.patch("api_blueprints.legalform_bp.execute_query", return_value=None)
    mocker.patch(
        "api_blueprints.legalform_bp.fetchone_query",
        return_value={"forma_giuridica": "SRL"},
    )
    token = create_access_token(identity={"role": "admin"})
    response = client.delete(
        "/legalform/SRL", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 204


def test_patch_legalform(client, mocker):
    mocker.patch("api_blueprints.legalform_bp.execute_query", return_value=None)
    mocker.patch(
        "api_blueprints.legalform_bp.fetchone_query",
        return_value={"forma_giuridica": "SRL"},
    )
    token = create_access_token(identity={"role": "admin"})
    response = client.patch(
        "/legalform/SRL",
        json={"forma_giuridica": "SPA"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json["outcome"] == "legal form successfully updated"


def test_options_legalform(client):
    response = client.options("/legalform")
    assert response.status_code == 200
    assert "Allow" in response.headers


def test_post_legalform_unauthorized(client):
    response = client.post("/legalform", json={"forma_giuridica": "SRL"})
    assert response.status_code == 401
    assert "error" in response.json
