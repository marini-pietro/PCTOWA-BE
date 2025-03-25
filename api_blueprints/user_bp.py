from flask import Blueprint, jsonify, request
from flask_restful import Api, Resource
from requests import post as requests_post
from config import API_SERVER_HOST, API_SERVER_PORT, API_SERVER_NAME_IN_LOG, AUTH_SERVER_HOST
import mysql.connector
from utils import fetchone_query, execute_query, log, jwt_required_endpoint  # Import shared utilities

# Create the blueprint and API
user_bp = Blueprint('user', __name__)
api = Api(user_bp)

class UserRegister(Resource):
    def post(self):
        email = request.json.get('email')
        password = request.json.get('password')
        name = request.json.get('nome')
        surname = request.json.get('cognome')
        user_type = request.json.get('tipo')

        try:
            execute_query(
                'INSERT INTO utenti (emailUtente, password, nome, cognome, tipo) VALUES (%s, %s, %s, %s, %s)',
                (email, password, name, surname, int(user_type))
            )

            # Log the register
            log(type='info', 
                message=f'User {email} registered', 
                origin_name=API_SERVER_NAME_IN_LOG, 
                origin_host=API_SERVER_HOST, 
                origin_port=API_SERVER_PORT)
            
            return jsonify({"outcome": "user successfully created"}), 201
        except mysql.connector.IntegrityError:
            return jsonify({'outcome': 'error, user with provided credentials already exists'}), 400

class UserLogin(Resource):
    def post(self):
        email = request.json.get('email')
        password = request.json.get('password')

        # Forward login request to the authentication service
        response = requests_post(f'{AUTH_SERVER_HOST}/auth/login', json={'email': email, 'password': password})
        if response.status_code == 200:
            return jsonify(response.json()), 200
        return jsonify({'error': 'Invalid credentials'}), 401

class UserUpdate(Resource):
    @jwt_required_endpoint
    def patch(self):
        email = request.args.get('email')
        to_modify = request.args.get('toModify')
        new_value = request.args.get('newValue')

        # Check if the field to modify is allowed
        if to_modify in ['email']:
            return jsonify({'outcome': 'error, specified field cannot be modified'})

        # Check if user exists
        user = fetchone_query('SELECT * FROM utente WHERE emailUtente = %s', (email,))
        if user is None:
            return jsonify({'outcome': 'error, user with provided email does not exist'})

        # Update the user
        execute_query(f'UPDATE utente SET {to_modify} = %s WHERE emailUtente = %s', (new_value, email))

        # Log the update
        log(type='info', 
            message=f'User {request.user_identity} updated', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        return jsonify({'outcome': 'user successfully updated'})

class UserDelete(Resource):
    @jwt_required_endpoint
    def delete(self):
        email = request.args.get('email')

        # Check if user exists
        user = fetchone_query('SELECT * FROM utente WHERE emailUtente = %s', (email,))
        if user is None:
            return jsonify({'outcome': 'error, user with provided email does not exist'})

        # Delete the user
        execute_query('DELETE FROM utente WHERE emailUtente = %s', (email,))

        # Log the deletion
        log(type='info', 
            message=f'User {request.user_identity} deleted', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        return jsonify({'outcome': 'user successfully deleted'})

# Add resources to the API
api.add_resource(UserRegister, '/register')
api.add_resource(UserLogin, '/login')
api.add_resource(UserUpdate, '/update')
api.add_resource(UserDelete, '/delete')