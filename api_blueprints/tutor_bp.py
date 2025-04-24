from os.path import basename as os_path_basename
from flask import Blueprint, request, Response
from flask_restful import Api, Resource
from flask_jwt_extended import get_jwt_identity
from typing import List, Dict, Union, Any
from .blueprints_utils import (check_authorization, fetchone_query, 
                               fetchall_query, execute_query, 
                               log, jwt_required_endpoint, 
                               create_response, has_valid_json, 
                               build_update_query_from_filters,
                               is_input_safe, get_class_http_verbs)
from config import (API_SERVER_HOST, API_SERVER_PORT, 
                    API_SERVER_NAME_IN_LOG, STATUS_CODES)

# Define constants
BP_NAME = os_path_basename(__file__).replace('_bp.py', '')

# Create the blueprint and API
tutor_bp = Blueprint(BP_NAME, __name__)
api = Api(tutor_bp)

class Tutor(Resource):

    ENDPOINT_PATHS = [f'/{BP_NAME}', f'/{BP_NAME}/<int:id>']

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor'])
    def post(self) -> Response:
        """
        Create a new tutor.
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
        nome: str = data.get('nome')
        cognome: str = data.get('cognome')
        telefono: str = data.get('telefono')
        email: str = data.get('email')

        # Insert the tutor
        lastrowid: int = execute_query(
            'INSERT INTO tutor (nome, cognome, telefonoTutor, emailTutor) VALUES (%s, %s, %s, %s)',
            (nome, cognome, telefono, email)
        )

        # Log the tutor creation
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} created tutor {lastrowid}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT,
            structured_data=f"[{Tutor.ENDPOINT_PATHS[0]} Verb POST]")

        # Return a success message
        return create_response(message={'outcome': 'tutor successfully created',
                                        'location': f'http://{API_SERVER_HOST}:{API_SERVER_PORT}/api/{BP_NAME}/{lastrowid}'}, status_code=STATUS_CODES["created"])

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor'])
    def delete(self, id) -> Response:
        """
        Delete a tutor by ID.
        The id must be provided as a path variable.
        """

        # Check if the tutor exists
        tutor: Dict[str, Any] = fetchone_query('SELECT nome FROM tutor WHERE idTutor = %s', (id,))
        if tutor is None:
            return create_response(message={'error': 'specified tutor does not exist'}, status_code=STATUS_CODES["not_found"])

        # Delete the tutor
        execute_query('DELETE FROM tutor WHERE idTutor = %s', (id,))

        # Log the deletion
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} deleted tutor {id}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT,
            structured_data=f"[{Tutor.ENDPOINT_PATHS[1]} Verb DELETE]")

        # Return a success message
        return create_response(message={'outcome': 'tutor successfully deleted'}, status_code=STATUS_CODES["no_content"])

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor'])
    def patch(self, id) -> Response:
        """
        Update a tutor by ID.
        The id must be provided as a path variable.
        """

        # Validate request
        data: Union[Dict[str, Any]] = has_valid_json(request)
        if isinstance(data, str): 
            return create_response(message={'error': data}, status_code=STATUS_CODES["bad_request"])

        # Check for sql injection
        if not is_input_safe(data):
            return create_response(message={'error': 'invalid input, suspected sql injection'}, status_code=STATUS_CODES["bad_request"])

        # Check if tutor exists
        tutor: Dict[str, Any] = fetchone_query('SELECT * FROM tutor WHERE idTutor = %s', (id,))
        if tutor is None:
            return create_response(message={'outcome': 'error, specified tutor does not exist'}, status_code=STATUS_CODES["not_found"])

        # Check that the specified fields actually exist in the database
        modifiable_columns: List[str] = ['nome', 'cognome', 'emailTutor', 'telefonoTutor']
        toModify: List[str]  = list(data.keys())
        error_columns: List[str] = [field for field in toModify if field not in modifiable_columns]
        if error_columns:
            return create_response(message={'outcome': f'error, field(s) {error_columns} do not exist or cannot be modified'}, status_code=STATUS_CODES["bad_request"])

        # Build the update query
        query, params = build_update_query_from_filters(data=data, table_name='tutor', 
                                                        id_column='idTutor', id_value=id)

        # Update the tutor
        execute_query(query, params)

        # Log the update
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} updated tutor {id}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT,
            structured_data=f"[{Tutor.ENDPOINT_PATHS[1]} Verb PATCH]")

        # Return a success message
        return create_response(message={'outcome': 'tutor successfully updated'}, status_code=STATUS_CODES["ok"])

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor', 'teacher'])
    def get(self, turn_id) -> Response:
        """
        Get a tutor by ID of its relative turn.
        The id must be provided as a path variable.
        """
        
        # Log the read
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} requested tutor list with turn id {turn_id}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT,
            structured_data=f"[{Tutor.ENDPOINT_PATHS[1]} Verb GET]")
        
        # Check that the specified company exists
        company: Dict[str, Any] = fetchone_query('SELECT * FROM aziende WHERE idAzienda = %s', (turn_id,))
        if not company:
            return create_response(message={'outcome': 'specified company not_found'}, status_code=STATUS_CODES["not_found"])
        
        # Get the data
        tutors: List[Dict[str, Any]] = fetchall_query(
            "SELECT TU.nome, TU.cognome, TU.emailTutor, TU.telefonoTutor "
            "FROM turni AS T JOIN turnoTutor AS TT ON T.idTurno = TT.idTurno "
            "JOIN tutor AS TU ON TU.idTutor = TT.idTutor "
            "WHERE T.idTurno = %s",  (turn_id, )
        )

        # Check if query returned any results
        if not tutors:
            return create_response(
                message={'outcome': 'no tutors found for specified turn'}, 
                status_code=STATUS_CODES["not_found"]
            )
        
        # Return the data
        return create_response(
            message=tutors,
            status_code=STATUS_CODES["ok"]
        )

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

api.add_resource(Tutor, *Tutor.ENDPOINT_PATHS)