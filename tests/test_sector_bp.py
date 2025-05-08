import pytest
from flask import Flask
from flask_jwt_extended import create_access_token
from api_blueprints.sector_bp import sector_bp


@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(sector_bp, url_prefix="/sector")
    app.config["JWT_SECRET_KEY"] = "test_secret"
    with app.test_client() as client:
        yield client


def test_post_sector(sector_client, mocker, admin_token):
    mocker.patch("api_blueprints.sector_bp.execute_query", return_value=1)
    response = sector_client.post(
        "/sector",
        json={"settore": "IT"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    assert response.json["outcome"] == "sector successfully created"


def test_get_sectors(client, mocker):
    mocker.patch(
        "api_blueprints.sector_bp.fetchall_query", return_value=[{"settore": "IT"}]
    )
    token = create_access_token(identity={"role": "admin"})
    response = client.get("/sector", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json[0]["settore"] == "IT"


def test_delete_sector(client, mocker):
    mocker.patch("api_blueprints.sector_bp.execute_query", return_value=None)
    mocker.patch(
        "api_blueprints.sector_bp.fetchone_query", return_value={"settore": "IT"}
    )
    token = create_access_token(identity={"role": "admin"})
    response = client.delete("/sector/IT", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 204


def test_patch_sector(client, mocker):
    mocker.patch("api_blueprints.sector_bp.execute_query", return_value=None)
    mocker.patch(
        "api_blueprints.sector_bp.fetchone_query", return_value={"settore": "IT"}
    )
    token = create_access_token(identity={"role": "admin"})
    response = client.patch(
        "/sector/IT",
        json={"settore": "Finance"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json["outcome"] == "sector successfully updated"


def test_options_sector(client):
    response = client.options("/sector")
    assert response.status_code == 200
    assert "Allow" in response.headers


def test_post_sector_unauthorized(client):
    response = client.post("/sector", json={"settore": "IT"})
    assert response.status_code == 401
    assert "error" in response.json
