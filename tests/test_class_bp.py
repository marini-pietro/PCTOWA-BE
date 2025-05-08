import pytest
from flask import Flask
from flask_jwt_extended import create_access_token
from api_blueprints.class_bp import class_bp


@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(class_bp, url_prefix="/class")
    app.config["JWT_SECRET_KEY"] = "test_secret"
    with app.test_client() as client:
        yield client


def test_post_class(client, mocker):
    mocker.patch("api_blueprints.class_bp.execute_query", return_value=1)
    token = create_access_token(identity={"role": "admin"})
    response = client.post(
        "/class",
        json={
            "sigla": "4A",
            "anno": "2024-2025",
            "email_responsabile": "teacher@example.com",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    assert response.json["outcome"] == "class created"


def test_get_class(client, mocker):
    mocker.patch(
        "api_blueprints.class_bp.fetchall_query", return_value=[{"sigla": "4A"}]
    )
    token = create_access_token(identity={"role": "admin"})
    response = client.get("/class/list", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json[0]["sigla"] == "4A"


def test_delete_class(client, mocker):
    mocker.patch("api_blueprints.class_bp.execute_query", return_value=None)
    mocker.patch("api_blueprints.class_bp.fetchone_query", return_value={"sigla": "4A"})
    token = create_access_token(identity={"role": "admin"})
    response = client.delete("/class/1", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 204


def test_patch_class(client, mocker):
    mocker.patch("api_blueprints.class_bp.execute_query", return_value=None)
    mocker.patch("api_blueprints.class_bp.fetchone_query", return_value={"sigla": "4A"})
    token = create_access_token(identity={"role": "admin"})
    response = client.patch(
        "/class/1", json={"sigla": "4B"}, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json["outcome"] == "class successfully updated"


def test_get_class_by_email(client, mocker):
    mocker.patch(
        "api_blueprints.class_bp.fetchone_query", return_value={"nome": "Teacher"}
    )
    mocker.patch(
        "api_blueprints.class_bp.fetchall_query",
        return_value=[
            {
                "sigla": "4A",
                "email_responsabile": "teacher@example.com",
                "anno": "2024-2025",
            }
        ],
    )
    token = create_access_token(identity={"role": "admin"})
    response = client.get(
        "/class/teacher@example.com", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json[0]["sigla"] == "4A"


def test_fuzzy_search_class(client, mocker):
    mocker.patch(
        "api_blueprints.class_bp.fetchall_query", return_value=[{"sigla": "4A"}]
    )
    token = create_access_token(identity={"role": "admin"})
    response = client.get(
        "/class/fsearch?fnome=4", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json[0]["sigla"] == "4A"


def test_list_classes(client, mocker):
    mocker.patch(
        "api_blueprints.class_bp.fetchall_query",
        return_value=[{"sigla": "4A"}, {"sigla": "4B"}],
    )
    token = create_access_token(identity={"role": "admin"})
    response = client.get("/class/list", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert len(response.json) == 2
    assert response.json[0]["sigla"] == "4A"
