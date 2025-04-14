from os.path import basename as os_path_basename
from flask import Blueprint, request, Response
from flask_restful import Api, Resource
from flask_jwt_extended import get_jwt_identity
from typing import List
from config import (API_SERVER_HOST, API_SERVER_PORT, 
                    API_SERVER_NAME_IN_LOG, STATUS_CODES)
from .blueprints_utils import (check_authorization, fetchone_query, 
                               fetchall_query, execute_query, 
                               log, jwt_required_endpoint, 
                               create_response, build_select_query_from_filters, 
                               build_update_query_from_filters)

# Define constants
BP_NAME = os_path_basename(__file__).replace('_bp.py', '')

# Create the blueprint and API
tutor_bp = Blueprint(BP_NAME, __name__)
api = Api(tutor_bp)

class Tutor(Resource):
    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor'])
    def post(self) -> Response:
        """
        Create a new tutor.
        The request body must be a JSON object with application/json content type.
        """
        # Ensure the request has a JSON body
        if not request.is_json or request.json is None:
            return create_response(message={'error': 'Request body must be valid JSON with Content-Type: application/json'}, status_code=STATUS_CODES["bad_request"])
        
        # Gather parameters
        nome = request.json.get('nome')
        cognome = request.json.get('cognome')
        telefono = request.json.get('telefono')
        email = request.json.get('email')

        # Insert the tutor
        lastrowid = execute_query(
            'INSERT INTO tutor (nome, cognome, telefonoTutor, emailTutor) VALUES (%s, %s, %s, %s)',
            (nome, cognome, telefono, email)
        )

        # Log the tutor creation
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} created tutor {lastrowid}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

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
        # Delete the tutor
        execute_query('DELETE FROM tutor WHERE idTutor = %s', (id,))

        # Log the deletion
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} deleted tutor {id}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        # Return a success message
        return create_response(message={'outcome': 'tutor successfully deleted'}, status_code=STATUS_CODES["no_content"])

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor'])
    def patch(self, id) -> Response:
        """
        Update a tutor by ID.
        The id must be provided as a path variable.
        """

        # Ensure the request has a JSON body
        if not request.is_json or request.json is None:
            return create_response(message={'error': 'Request body must be valid JSON with Content-Type: application/json'}, status_code=STATUS_CODES["bad_request"])

        # Check if tutor exists
        tutor = fetchone_query('SELECT * FROM tutor WHERE idTutor = %s', (id,))
        if tutor is None:
            return create_response(message={'outcome': 'error, specified tutor does not exist'}, status_code=STATUS_CODES["not_found"])

        # Check that the specified fields actually exist in the database
        modifiable_columns: List[str] = ['nome', 'cognome', 'emailTutor', 'telefonoTutor']
        toModify: list[str]  = list(request.json.keys())
        error_columns = [field for field in toModify if field not in modifiable_columns]
        if error_columns:
            return create_response(message={'outcome': f'error, field(s) {error_columns} do not exist or cannot be modified'}, status_code=STATUS_CODES["bad_request"])

        # Build the update query
        query, params = build_update_query_from_filters(data=request.json, table_name='tutor', 
                                                        id_column='idTutor', id_value=id)

        # Update the tutor
        execute_query(query, params)

        # Log the update
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} updated tutor {id}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

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
            origin_port=API_SERVER_PORT)
        
        # Check that the specified company exists
        company = fetchone_query('SELECT * FROM aziende WHERE idAzienda = %s', (turn_id,))
        if not company:
            return create_response(message={'outcome': 'specified company not_found'}, status_code=STATUS_CODES["not_found"])
        
        # Get the data
        tutors = fetchall_query(
            "SELECT TU.nome, TU.cognome, TU.emailTutor, TU.telefonoTutor " \
            "FROM turni AS T JOIN turnoTutor AS TT ON T.idTurno = TT.idTurno" \
            "JOIN tutor AS TU ON TU.idTutor = TT.idTutor" \
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

api.add_resource(Tutor, f'/{BP_NAME}', f'/{BP_NAME}/<int:id>')