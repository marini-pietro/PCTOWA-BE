import pytest
from flask import Flask
from flask_jwt_extended import create_access_token
from api_blueprints.address_bp import address_bp

@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(address_bp, url_prefix='/address')
    app.config['JWT_SECRET_KEY'] = 'test_secret'
    with app.test_client() as client:
        yield client

def test_post_address(client, mocker):
    mocker.patch('api_blueprints.address_bp.execute_query', return_value=1)
    token = create_access_token(identity={"role": "admin"})
    response = client.post(
        '/address',
        json={"stato": "Italy", "provincia": "Rome", "comune": "Rome", "cap": "00100", "indirizzo": "Via Roma"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    assert response.json['outcome'] == 'address successfully created'

def test_get_address(client, mocker):
    mocker.patch('api_blueprints.address_bp.fetchone_query', return_value={"stato": "Italy"})
    token = create_access_token(identity={"role": "admin"})
    response = client.get('/address/1', headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json['stato'] == 'Italy'

def test_delete_address(client, mocker):
    mocker.patch('api_blueprints.address_bp.execute_query', return_value=None)
    mocker.patch('api_blueprints.address_bp.fetchone_query', return_value={"stato": "Italy"})
    token = create_access_token(identity={"role": "admin"})
    response = client.delete('/address/1', headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 204

def test_patch_address(client, mocker):
    mocker.patch('api_blueprints.address_bp.execute_query', return_value=None)
    mocker.patch('api_blueprints.address_bp.fetchone_query', return_value={"stato": "Italy"})
    token = create_access_token(identity={"role": "admin"})
    response = client.patch(
        '/address/1',
        json={"indirizzo": "Via Milano"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json['outcome'] == 'address successfully updated'

def test_options_address(client):
    response = client.options('/address')
    assert response.status_code == 200
    assert 'Allow' in response.headers

def test_post_address_unauthorized(client):
    response = client.post(
        '/address',
        json={"stato": "Italy", "provincia": "Rome", "comune": "Rome", "cap": "00100", "indirizzo": "Via Roma"}
    )
    assert response.status_code == 401
    assert 'error' in response.json