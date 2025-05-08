import pytest
from flask import Flask
from flask_jwt_extended import create_access_token
from api_blueprints.user_bp import user_bp

@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(user_bp, url_prefix='/user')
    app.config['JWT_SECRET_KEY'] = 'test_secret'
    with app.test_client() as client:
        yield client

def test_post_user(user_client, mocker, admin_token):
    mocker.patch('api_blueprints.user_bp.execute_query', return_value=1)
    response = user_client.post(
        '/user',
        json={"email": "user@example.com", "password": "password123", "name": "John", "surname": "Doe"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 201
    assert response.json['outcome'] == 'user successfully created'

def test_get_user(client, mocker):
    mocker.patch('api_blueprints.user_bp.fetchall_query', return_value=[{"email": "user@example.com"}])
    token = create_access_token(identity={"role": "admin"})
    response = client.get('/user/binded/1', headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json[0]['email'] == 'user@example.com'

def test_delete_user(client, mocker):
    mocker.patch('api_blueprints.user_bp.execute_query', return_value=None)
    mocker.patch('api_blueprints.user_bp.fetchone_query', return_value={"email": "user@example.com"})
    token = create_access_token(identity={"role": "admin"})
    response = client.delete('/user/user@example.com', headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 204

def test_patch_user(client, mocker):
    mocker.patch('api_blueprints.user_bp.execute_query', return_value=None)
    mocker.patch('api_blueprints.user_bp.fetchone_query', return_value={"email": "user@example.com"})
    token = create_access_token(identity={"role": "admin"})
    response = client.patch(
        '/user/user@example.com',
        json={"name": "Jane"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json['outcome'] == 'user successfully updated'

def test_options_user(client):
    response = client.options('/user')
    assert response.status_code == 200
    assert 'Allow' in response.headers

def test_post_user_unauthorized(client):
    response = client.post(
        '/user',
        json={"email": "user@example.com", "password": "password123", "name": "John", "surname": "Doe"}
    )
    assert response.status_code == 401
    assert 'error' in response.json