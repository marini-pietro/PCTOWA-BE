import pytest
from flask import Flask
from flask_jwt_extended import create_access_token
from api_blueprints.turn_bp import turn_bp

@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(turn_bp, url_prefix='/turn')
    app.config['JWT_SECRET_KEY'] = 'test_secret'
    with app.test_client() as client:
        yield client

def test_post_turn(client, mocker):
    mocker.patch('api_blueprints.turn_bp.execute_query', return_value=1)
    token = create_access_token(identity={"role": "admin"})
    response = client.post(
        '/turn',
        json={"data_inizio": "2025-05-01", "data_fine": "2025-05-31", "settore": "IT"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    assert response.json['outcome'] == 'turn successfully created'

def test_get_turn(client, mocker):
    mocker.patch('api_blueprints.turn_bp.fetchall_query', return_value=[{"id_turno": 1}])
    token = create_access_token(identity={"role": "admin"})
    response = client.get('/turn/1', headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json[0]['id_turno'] == 1

def test_delete_turn(client, mocker):
    mocker.patch('api_blueprints.turn_bp.execute_query', return_value=None)
    mocker.patch('api_blueprints.turn_bp.fetchone_query', return_value={"id_turno": 1})
    token = create_access_token(identity={"role": "admin"})
    response = client.delete('/turn/1', headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 204

def test_patch_turn(client, mocker):
    mocker.patch('api_blueprints.turn_bp.execute_query', return_value=None)
    mocker.patch('api_blueprints.turn_bp.fetchone_query', return_value={"id_turno": 1})
    token = create_access_token(identity={"role": "admin"})
    response = client.patch(
        '/turn/1',
        json={"settore": "Finance"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json['outcome'] == 'turn successfully updated'

def test_options_turn(client):
    response = client.options('/turn')
    assert response.status_code == 200
    assert 'Allow' in response.headers

def test_post_turn_unauthorized(client):
    response = client.post(
        '/turn',
        json={"data_inizio": "2025-05-01", "data_fine": "2025-05-31", "settore": "IT"}
    )
    assert response.status_code == 401
    assert 'error' in response.json