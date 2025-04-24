from os.path import basename as os_path_basename
from flask import Blueprint, request, Response
from flask_restful import Api, Resource
from flask_jwt_extended import get_jwt_identity
from requests import post as requests_post
from requests.exceptions import RequestException
from mysql.connector import IntegrityError
from typing import List, Dict, Any, Union
from .blueprints_utils import (check_authorization, fetchone_query, 
                               fetchall_query, execute_query, 
                               log, jwt_required_endpoint, 
                               create_response, build_update_query_from_filters,
                               has_valid_json, is_input_safe,
                               get_class_http_verbs)
from config import (API_SERVER_HOST, API_SERVER_PORT, 
                    API_SERVER_NAME_IN_LOG, AUTH_SERVER_HOST, 
                    AUTH_SERVER_PORT, STATUS_CODES)

# Define constants
BP_NAME = os_path_basename(__file__).replace('_bp.py', '')

# Create the blueprint and API
user_bp = Blueprint(BP_NAME, __name__)
api = Api(user_bp)

class User(Resource):

    ENDPOINT_PATHS = [f'/{BP_NAME}', f'/{BP_NAME}/<string:email>']

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin'])
    def post(self) -> Response:
        """
        Register a new user.
        The request body must be a JSON object with application/json content type.
        """
        
        # Validate request
        data: Union[str, Dict[str, Any]] = has_valid_json(request)
        if isinstance(data, str): 
            return create_response(message={'error': data}, status_code=STATUS_CODES["bad_request"])
        
        # Check for sql injection
        if not is_input_safe(data):
            return create_response(message={'error': 'invalid input, suspected sql injection'}, status_code=STATUS_CODES["bad_request"])

        # Gather parameters
        email: str = data.get('email')
        password: str = data.get('password')
        name: str = data.get('nome')
        surname: str = data.get('cognome')
        user_type: int = data.get('tipo')

        try:
            lastrowid: int = execute_query(
                'INSERT INTO utenti (emailUtente, password, nome, cognome, tipo) VALUES (%s, %s, %s, %s, %s)',
                (email, password, name, surname, int(user_type))
            )
        
            # Log the register
            log(type='info', 
                message=f'User {get_jwt_identity().get("email")} registered user {email}', 
                origin_name=API_SERVER_NAME_IN_LOG, 
                origin_host=API_SERVER_HOST, 
                origin_port=API_SERVER_PORT,
                structured_data=f"[{User.ENDPOINT_PATHS[0]} Verb POST]")
            
            # Return success message
            return create_response(message={"outcome": "user successfully created",
                                            'location': f'http://{API_SERVER_HOST}:{API_SERVER_PORT}/api/{BP_NAME}/{lastrowid}'}, status_code=STATUS_CODES["created"])
        except IntegrityError as ex:
            return create_response(message={'outcome': 'error, user with provided credentials already exists'}, status_code=STATUS_CODES["bad_request"])

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin'])
    def delete(self, email) -> Response:
        """
        Delete an existing user.
        The id is passed as a path variable.
        """

        # Check if user exists
        user: Dict[str, Any] = fetchone_query('SELECT nome FROM utente WHERE emailUtente = %s', (email,))
        if user is None:
            return create_response(message={'error': 'user with provided email does not exist'}, status_code=STATUS_CODES["not_found"])

        # Delete the user
        execute_query('DELETE FROM utente WHERE emailUtente = %s', (email,))

        # Log the deletion
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} deleted user {email}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT,
            structured_data=f"[{User.ENDPOINT_PATHS[1]} Verb DELETE]")

        # Return success message
        return create_response(message={'outcome': 'user successfully deleted'}, status_code=STATUS_CODES["no_content"])

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin'])
    def patch(self, email) -> Response:
        """
        Update an existing user.
        The id is passed as a path variable.
        """

        # Validate request
        data: Union[str, Dict[str, Any]] = has_valid_json(request)
        if isinstance(data, str): 
            return create_response(message={'error': data}, status_code=STATUS_CODES["bad_request"])

        # Check for sql injection
        if not is_input_safe(data):
            return create_response(message={'error': 'invalid input, suspected sql injection'}, status_code=STATUS_CODES["bad_request"])

        # Check if user exists
        user: Dict[str, Any] = fetchone_query('SELECT * FROM utente WHERE emailUtente = %s', (email,))
        if user is None:
            return create_response(message={'outcome': 'error, user with provided email does not exist'}, status_code=STATUS_CODES["not_found"])

        # Check that the specified fields actually exist in the database
        modifiable_columns: List[str] = ['emailUtente', 'password', 'nome', 'cognome', 'tipo']
        toModify: List[str]  = list(data.keys())
        error_columns: List[str] = [field for field in toModify if field not in modifiable_columns]
        if error_columns:
            return create_response(message={'outcome': f'error, field(s) {error_columns} do not exist or cannot be modified'}, status_code=STATUS_CODES["bad_request"])

        # Build the update query
        query, params = build_update_query_from_filters(data=data, table_name='utenti', 
                                                        id_column='emailUtente', id_value=email)

        # Update the user
        execute_query(query, params)

        # Log the update
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} updated user {email}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT,
            structured_data=f"[{User.ENDPOINT_PATHS[1]} Verb PATCH]")

        # Return success message
        return create_response(message={'outcome': 'user successfully updated'}, status_code=STATUS_CODES["ok"])

    # TODO GET method to get all user for an admin page???

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor', 'teacher'])
    def options(self) -> Response:
        # Define allowed methods
        allowed_methods = get_class_http_verbs(type(self))
        
        # Create the response
        response = Response(status=STATUS_CODES["ok"])
        response.headers['Allow'] = ', '.join(allowed_methods)
        response.headers['Access-Control-Allow-Origin'] = '*'  # Adjust as needed for CORS
        response.headers['Access-Control-Allow-Methods'] = ', '.join(allowed_methods)
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        
        return response

class UserLogin(Resource):

    ENDPOINT_PATHS = [f'/{BP_NAME}/auth/login']

    def post(self) -> Response:
        """
        User login endpoint.
        The request body must be a JSON object with application/json content type.
        """

        # Validate request
        data: Union[str,  Dict[str, Any]] = has_valid_json(request)
        if isinstance(data, str): 
            return create_response(message={'error': data}, status_code=STATUS_CODES["bad_request"])
        
        # Check for sql injection
        if not is_input_safe(data):
            return create_response(message={'error': 'invalid input, suspected sql injection'}, status_code=STATUS_CODES["bad_request"])

        # Gather parameters
        email: str = data.get('email')
        password: str = data.get('password')
        
        # Validate parameters
        if email is None or password is None or email == '' or password == '':
            return create_response(message={'error': 'missing email or password'}, status_code=STATUS_CODES["bad_request"])

        try:
            # Forward login request to the authentication service
            response = requests_post(f'http://{AUTH_SERVER_HOST}:{AUTH_SERVER_PORT}/auth/login', json={'email': email, 'password': password}, timeout=5)
        except RequestException as e:
            return create_response(message={'error': 'Authentication service unavailable'}, status_code=STATUS_CODES["internal_error"])

        # Handle response from the authentication service
        if response.status_code == STATUS_CODES["ok"]:  # If the login is successful, send the token back to the user

            log(type='info',
                message=f'User {get_jwt_identity().get("email")} logged in successfully with email: {email}', 
                origin_name=API_SERVER_NAME_IN_LOG, 
                origin_host=API_SERVER_HOST, 
                origin_port=API_SERVER_PORT,
                structured_data=f"[{UserLogin.ENDPOINT_PATHS[0]} Verb POST]")

            return create_response(message=response.json(), status_code=STATUS_CODES["ok"])
        
        elif response.status_code == STATUS_CODES["unauthorized"]:
            log(type='warning', 
            message=f'Failed login attempt for email: {email}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT,
            structured_data=f"[{UserLogin.ENDPOINT_PATHS[0]} Verb POST]")
            return create_response(message={'error': 'Invalid credentials'}, status_code=STATUS_CODES["unauthorized"])
        
        elif response.status_code == STATUS_CODES["bad_request"]:
            log(type='error', 
            message=f'Bad request during login for email: {email}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT,
            structured_data=f"[{UserLogin.ENDPOINT_PATHS[0]} Verb POST]")
            return create_response(message={'error': 'Bad request'}, status_code=STATUS_CODES["bad_request"])
        
        elif response.status_code == STATUS_CODES["internal_error"]:
            log(type='error', 
            message=f'Internal error during login for email: {email}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT,
            structured_data=f"[{UserLogin.ENDPOINT_PATHS[0]} Verb POST]")
            return create_response(message={'error': 'Internal error'}, status_code=STATUS_CODES["internal_error"])
        
        else:
            log(type='error', 
            message=f'Unexpected error during login for email: {email} with status code: {response.status_code}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT,
            structured_data=f"[{UserLogin.ENDPOINT_PATHS[0]} Verb POST]")
            return create_response(message={'error': 'Unexpected error during login'}, status_code=STATUS_CODES["internal_error"])

    def options(self) -> Response:
        # Define allowed methods
        allowed_methods = get_class_http_verbs(type(self))
        
        # Create the response
        response = Response(status=STATUS_CODES["ok"])
        response.headers['Allow'] = ', '.join(allowed_methods)
        response.headers['Access-Control-Allow-Origin'] = '*'  # Adjust as needed for CORS
        response.headers['Access-Control-Allow-Methods'] = ', '.join(allowed_methods)
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        
        return response

class BindUserToCompany(Resource):

    ENDPOINT_PATHS = [f'/{BP_NAME}/bind/<string:email>']

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin'])
    def post(self, email) -> Response:
        """
        Bind a user to a company.
        The id is passed as a path variable.
        """

        # Validate request
        data: Union[str,  Dict[str, Any]] = has_valid_json(request)
        if isinstance(data, str): 
            return create_response(message={'error': data}, status_code=STATUS_CODES["bad_request"])

        # Check for sql injection
        if not is_input_safe(data):
            return create_response(message={'error': 'invalid input, suspected sql injection'}, status_code=STATUS_CODES["bad_request"])

        # Gather parameters
        company_id: Union[str, int] = data.get('idAzienda')

        # Validate parameters
        if company_id is None:
            return create_response(message={'error': 'missing company id'}, status_code=STATUS_CODES["bad_request"])
        try:
            company_id = int(company_id)
        except ValueError:
            return create_response(message={'error': 'company id must be an integer'}, status_code=STATUS_CODES["bad_request"])

        # Check if user exists
        user: Dict[str, Any] = fetchone_query('SELECT * FROM utenti WHERE emailUtente = %s', (email,))
        if user is None:
            return create_response(message={'outcome': 'error, user with provided email does not exist'}, status_code=STATUS_CODES["not_found"])
        
        # Check if company exists
        company: Dict[str, Any] = fetchone_query('SELECT * FROM aziende WHERE idAzienda = %s', (company_id,))
        if company is None:
            return create_response(message={'outcome': 'error, company with provided id does not exist'}, status_code=STATUS_CODES["not_found"])

        # Bind the user to the company
        try:
            execute_query('UPDATE utenti SET company_id = %s WHERE emailUtente = %s', (company_id, email))
        except IntegrityError as ex:
            log(type='error',
                message=f'User {get_jwt_identity().get("email")} tried to bind user {email} to company {company_id} but it already generated {ex}',
                origin_name=API_SERVER_NAME_IN_LOG, 
                origin_host=API_SERVER_HOST, 
                origin_port=API_SERVER_PORT)
            return create_response(message={'error': 'conflict error'}, status_code=STATUS_CODES["conflict"])
        except Exception as ex:
            log(type='error',
                message=f'User {get_jwt_identity().get("email")} failed to bind user {email} to company {company_id} with error: {str(ex)}',
                origin_name=API_SERVER_NAME_IN_LOG, 
                origin_host=API_SERVER_HOST, 
                origin_port=API_SERVER_PORT)
            return create_response(message={'error': "internal server error"}, status_code=STATUS_CODES["internal_error"])

        # Log the binding
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} bound user {email} to company {company_id}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT,
            structured_data=f"[{BindUserToCompany.ENDPOINT_PATHS[0]} Verb POST]")

        # Return success message
        return create_response(message={'outcome': 'user successfully bound to company'}, status_code=STATUS_CODES["ok"])

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor', 'teacher'])
    def options(self) -> Response:
        # Define allowed methods
        allowed_methods = get_class_http_verbs(type(self))
        
        # Create the response
        response = Response(status=STATUS_CODES["ok"])
        response.headers['Allow'] = ', '.join(allowed_methods)
        response.headers['Access-Control-Allow-Origin'] = '*'  # Adjust as needed for CORS
        response.headers['Access-Control-Allow-Methods'] = ', '.join(allowed_methods)
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        
        return response

class ReadBindedUser(Resource):

    ENDPOINT_PATHS = [f'/{BP_NAME}/bind/<string:id>']

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor', 'teacher'])
    def get(self, id) -> Response:
        """
        Get the list of the reference teachers associated with a given company or class.
        The company or class is passed as a path variable id.
        The id_type is passed as a query parameter.
        The id_type can be either 'company' or 'class'.
        """
        
        # Log the read
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} requested reference teacher list with {id_type} and id {id}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT,
            structured_data=f"[{ReadBindedUser.ENDPOINT_PATHS[0]} Verb GET]")

        # Gather parameters
        id_type: str = request.args.get('id_type')

        # Validate parameters
        if id_type is None:
            return create_response(message={'error': 'missing id_type'}, status_code=STATUS_CODES["bad_request"])
        if id_type not in ['company', 'class']:
            return create_response(message={'error': 'id_type must be either company or class'}, status_code=STATUS_CODES["bad_request"])

        # Check that the specified resource exist
        if id_type == 'company':
            company: Dict[str, Any] = fetchone_query('SELECT * FROM aziende WHERE idAzienda = %s', (id,))
            if not company:
                return create_response(message={'outcome': 'error, specified company does not exist'}, status_code=STATUS_CODES["not_found"])
        
            # Build query
            query: str = (
                "SELECT U.emailUtente, U.nome, U.cognome, RT.anno "
                "FROM docenteReferente AS RT JOIN utenti AS U ON U.emailUtente = RT.docenteReferente "
                "WHERE RT.idAzienda = %s"
            )
            
        # Check that the specified resource exist
        elif id_type == 'class':
            class_: Dict[str, Any] = fetchone_query('SELECT * FROM classi WHERE idClasse = %s', (id,))
            if not class_:
                return create_response(message={'outcome': 'error, specified class does not exist'}, status_code=STATUS_CODES["not_found"])
      
            query: str = (
                    "SELECT U.emailUtente, U.nome, U.cognome, C.anno "
                    "FROM classi AS C JOIN utenti AS U ON U.emailUtente = C.emailResponsabile "
                    "WHERE C.idClasse = %s"
            )

        # Get the list of associated users
        resources: List[Dict[str, Any]] = fetchall_query(query, (id,))
        
        # Return the list of users
        return create_response(message=resources, status_code=STATUS_CODES["ok"])

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor', 'teacher'])
    def options(self) -> Response:
        # Define allowed methods
        allowed_methods = get_class_http_verbs(type(self))
        
        # Create the response
        response = Response(status=STATUS_CODES["ok"])
        response.headers['Allow'] = ', '.join(allowed_methods)
        response.headers['Access-Control-Allow-Origin'] = '*'  # Adjust as needed for CORS
        response.headers['Access-Control-Allow-Methods'] = ', '.join(allowed_methods)
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        
        return response

# Add resources to the API
api.add_resource(User, *User.ENDPOINT_PATHS)
api.add_resource(UserLogin, *UserLogin.ENDPOINT_PATHS)
api.add_resource(BindUserToCompany, *BindUserToCompany.ENDPOINT_PATHS)
api.add_resource(ReadBindedUser, *ReadBindedUser.ENDPOINT_PATHS)