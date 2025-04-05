from flask import Blueprint, request
from flask_restful import Api, Resource
from flask_jwt_extended import get_jwt_identity
from requests import post as requests_post
from requests.exceptions import RequestException
from config import (API_SERVER_HOST, API_SERVER_PORT, 
                    API_SERVER_NAME_IN_LOG, AUTH_SERVER_HOST, 
                    AUTH_SERVER_PORT, STATUS_CODES)
from .blueprints_utils import (check_authorization, validate_filters, 
                               fetchone_query, fetchall_query, 
                               execute_query, log, 
                               jwt_required_endpoint, create_response, 
                               build_update_query_from_filters, build_select_query_from_filters)

# Create the blueprint and API
user_bp = Blueprint('user', __name__)
api = Api(user_bp)

class UserRegister(Resource):
    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin'])
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
            
            # Return success message
            return create_response(message={"outcome": "user successfully created"}, status_code=STATUS_CODES["created"])
        except Exception:
            return create_response(message={'outcome': 'error, user with provided credentials already exists'}, status_code=STATUS_CODES["bad_request"])

class UserLogin(Resource):
    def post(self):
        # Gather parameters
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        # Validate parameters
        if email is None or password is None:
            return create_response(message={'error': 'missing email or password'}, status_code=STATUS_CODES["bad_request"])

        try:
            # Forward login request to the authentication service
            response = requests_post(f'http://{AUTH_SERVER_HOST}:{AUTH_SERVER_PORT}/auth/login', json={'email': email, 'password': password}, timeout=5)
        except RequestException as e:
            return create_response(message={'error': 'Authentication service unavailable'}, status_code=STATUS_CODES["internal_error"])

        # Handle response from the authentication service
        if response.status_code == STATUS_CODES["ok"]:  # If the login is successful, send the token back to the user
            return create_response(message=response.json(), status_code=STATUS_CODES["ok"])
        elif response.status_code == STATUS_CODES["unauthorized"]:
            log(type='warning', 
            message=f'Failed login attempt for email: {email}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)
            return create_response(message={'error': 'Invalid credentials'}, status_code=STATUS_CODES["unauthorized"])
        elif response.status_code == STATUS_CODES["bad_request"]:
            log(type='error', 
            message=f'Bad request during login for email: {email}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)
            return create_response(message={'error': 'Bad request'}, status_code=STATUS_CODES["bad_request"])
        elif response.status_code == STATUS_CODES["internal_error"]:
            log(type='error', 
            message=f'Internal error during login for email: {email}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)
            return create_response(message={'error': 'Internal error'}, status_code=STATUS_CODES["internal_error"])
        else:
            log(type='error', 
            message=f'Unexpected error during login for email: {email} with status code: {response.status_code}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)
            return create_response(message={'error': 'Unexpected error during login'}, status_code=STATUS_CODES["internal_error"])

class UserUpdate(Resource):
    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin'])
    def patch(self):
        email = request.args.get('email')
        toModify: list[str] = request.args.get('toModify').split(',')
        newValues: list[str] = request.args.get('newValue').split(',')

        # Validate parameters
        if len(toModify) != len(newValues):
            return create_response(message={'outcome': 'Mismatched fields and values lists lengths'}, status_code=STATUS_CODES["bad_request"])

        # Build a dictionary with fields as keys and values as values
        updates = dict(zip(toModify, newValues))  # {field1: value1, field2: value2, ...}

        # Check that the specified fields can be modified (in this case all fields can be modified)

        # Check that the specified fields actually exist in the database
        outcome = validate_filters(data=updates, table_name='utenti')
        if outcome is not True:  # if the validation fails, outcome will be a dict with the error message
            return create_response(outcome, STATUS_CODES["bad_request"])

        # Check if user exists
        user = fetchone_query('SELECT * FROM utente WHERE emailUtente = %s', (email,))
        if user is None:
            return create_response(message={'outcome': 'error, user with provided email does not exist'}, status_code=STATUS_CODES["not_found"])

        # Build the update query
        query, params = build_update_query_from_filters(data=updates, table_name='utenti', id=email)

        # Update the user
        execute_query(query, params)

        # Log the update
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} updated user {email}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        # Return success message
        return create_response(message={'outcome': 'user successfully updated'}, status_code=STATUS_CODES["ok"])

class UserDelete(Resource):
    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin'])
    def delete(self):
        # Gather parameters
        email = request.args.get('email')

        # Validate parameters
        if email is None:
            return create_response(message={'error': 'missing email'}, status_code=STATUS_CODES["bad_request"])

        # Delete the user
        execute_query('DELETE FROM utente WHERE emailUtente = %s', (email,))

        # Log the deletion
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} deleted user {email}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        # Return success message
        return create_response(message={'outcome': 'user successfully deleted'}, status_code=STATUS_CODES["no_content"])
    
class UserRead(Resource):
    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor', 'teacher'])
    def get(self):
        # Gather parameters
        email = request.args.get('email')
        password = request.args.get('password')
        nome = request.args.get('nome')
        cognome = request.args.get('cognome')
        try:
            tipo = int(request.args.get('tipo'))
        except (ValueError, TypeError):
            return create_response(message={'error': 'invalid tipo parameter'}, status_code=STATUS_CODES["bad_request"])
        try:
            limit = int(request.args.get('limit'))
            offset = int(request.args.get('offset'))
        except (ValueError, TypeError):
            return create_response(message={'error': 'invalid limit or offset parameter'}, status_code=STATUS_CODES["bad_request"])

        # Build the filters dictionary (only include non-null values)
        data = {key: value for key, value in {
            'emailUtente': email,
            'password': password,
            'nome': nome,
            'cognome': cognome,
            'tipo': tipo
        }.items() if value}

        try:
            # Build the query
            query, params = build_update_query_from_filters(
                data=data, 
                table_name='utenti',
                limit=limit, 
                offset=offset
            )

            # Execute query
            users = fetchall_query(query, params)

            # Get the ids to log
            ids = [user['emailUtente'] for user in users]

            # Log the read
            log(type='info', 
                message=f'User {get_jwt_identity().get("email")} read users {ids}', 
                origin_name=API_SERVER_NAME_IN_LOG, 
                origin_host=API_SERVER_HOST, 
                origin_port=API_SERVER_PORT)

            # Return the users
            return create_response(message=users, status_code=STATUS_CODES["ok"])
        except Exception as err:
            return create_response(message={'error': str(err)}, status_code=STATUS_CODES["internal_error"])

# Add resources to the API
api.add_resource(UserRegister, '/register')
api.add_resource(UserLogin, '/login')
api.add_resource(UserRead, '/read')
api.add_resource(UserUpdate, '/update')
api.add_resource(UserDelete, '/delete')