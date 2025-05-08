import pytest
from flask import Flask
from flask_jwt_extended import create_access_token
from api_blueprints.student_bp import student_bp

@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(student_bp, url_prefix='/student')
    app.config['JWT_SECRET_KEY'] = 'test_secret'
    with app.test_client() as client:
        yield client

def test_post_student(client, mocker):
    mocker.patch('api_blueprints.student_bp.execute_query', return_value=1)
    token = create_access_token(identity={"role": "admin"})
    response = client.post(
        '/student',
        json={"matricola": "12345", "nome": "John", "cognome": "Doe", "id_classe": 1},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    assert response.json['outcome'] == 'student successfully created'

def test_get_student(client, mocker):
    mocker.patch('api_blueprints.student_bp.fetchall_query', return_value=[{"matricola": "12345"}])
    token = create_access_token(identity={"role": "admin"})
    response = client.get('/student/class/1', headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json['12345']['nome'] == 'John'

def test_delete_student(client, mocker):
    mocker.patch('api_blueprints.student_bp.execute_query', return_value=None)
    mocker.patch('api_blueprints.student_bp.fetchone_query', return_value={"matricola": "12345"})
    token = create_access_token(identity={"role": "admin"})
    response = client.delete('/student/12345', headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 204

def test_patch_student(client, mocker):
    mocker.patch('api_blueprints.student_bp.execute_query', return_value=None)
    mocker.patch('api_blueprints.student_bp.fetchone_query', return_value={"matricola": "12345"})
    token = create_access_token(identity={"role": "admin"})
    response = client.patch(
        '/student/12345',
        json={"nome": "Jane"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json['outcome'] == 'student successfully updated'

def test_options_student(client):
    response = client.options('/student')
    assert response.status_code == 200
    assert 'Allow' in response.headers

def test_post_student_unauthorized(client):
    response = client.post(
        '/student',
        json={"matricola": "12345", "nome": "John", "cognome": "Doe", "id_classe": 1}
    )
    assert response.status_code == 401
    assert 'error' in response.json