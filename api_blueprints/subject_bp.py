from os.path import basename as os_path_basename
from flask import Blueprint, request, Response
from flask_restful import Api, Resource
from flask_jwt_extended import get_jwt_identity
from typing import List, Dict, Union, Any
from re import match as re_match
from mysql.connector import IntegrityError
from .blueprints_utils import (check_authorization, fetchone_query, 
                               fetchall_query, execute_query, 
                               log, jwt_required_endpoint, 
                               create_response, build_update_query_from_filters, 
                               build_select_query_from_filters, has_valid_json,
                               is_input_safe, get_class_http_verbs)
from config import (API_SERVER_HOST, API_SERVER_PORT, 
                    API_SERVER_NAME_IN_LOG, STATUS_CODES)

# Define constants
BP_NAME = os_path_basename(__file__).replace('_bp.py', '')

# Create the blueprint and API
subject_bp = Blueprint(BP_NAME, __name__)
api = Api(subject_bp)

class Subject(Resource):

    ENDPOINT_PATHS = [f'/{BP_NAME}/<string:materia>']

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin'])
    def post(self, materia) -> Response:
        """
        Create a new subject.
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
        descrizione: str = data.get('descrizione')
        hexColor: str = data.get('hexColor')

        # Validate parameters
        if not isinstance(materia, str):
            return create_response(message={'error': 'materia must be a string'}, status_code=STATUS_CODES["bad_request"])
        if len(materia) > 255:
            return create_response(message={'error': 'materia too long'}, status_code=STATUS_CODES["bad_request"])
        if not isinstance(descrizione, str):
            return create_response(message={'error': 'descrizione must be a string'}, status_code=STATUS_CODES["bad_request"])
        if len(descrizione) > 255:
            return create_response(message={'error': 'descrizione too long'}, status_code=STATUS_CODES["bad_request"])
        if not isinstance(hexColor, str):
            return create_response(message={'error': 'hexColor must be a string'}, status_code=STATUS_CODES["bad_request"])
        if not re_match(r'^#[0-9A-Fa-f]{6}$', hexColor):
            return create_response(message={'outcome': 'invalid hexColor format'}, status_code=STATUS_CODES["bad_request"])

        # Insert the subject
        try:
            lastrowid: int = execute_query('INSERT INTO materie (materia, descrizione, hexColor) VALUES (%s, %s, %s)', (materia, descrizione, hex))

            # Log the subject creation
            log(type='info', 
                message=f'User {get_jwt_identity().get("email")} created subject {materia}', 
                origin_name=API_SERVER_NAME_IN_LOG, 
                origin_host=API_SERVER_HOST, 
                origin_port=API_SERVER_PORT,
                structured_data=f"[{Subject.ENDPOINT_PATHS[0]} Verb POST]")

            # Return a success message
            return create_response(message={'outcome': 'subject successfully created',
                                            'location': f'http://{API_SERVER_HOST}:{API_SERVER_PORT}/api/{BP_NAME}/{lastrowid}'}, status_code=STATUS_CODES["created"])

        except IntegrityError as ex:
            log(type='error',
                message=f'User {get_jwt_identity().get("email")} tried to create subject {materia} but it already generated {ex}',
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                origin_port=API_SERVER_PORT,
                structured_data=f"[{Subject.ENDPOINT_PATHS[0]} Verb POST]")
            return create_response(message={'error': 'conflict error'}, status_code=STATUS_CODES["conflict"])
        except Exception as ex:
            log(type='error',
                message=f'User {get_jwt_identity().get("email")} failed to create subject {materia} with error: {str(ex)}',
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                origin_port=API_SERVER_PORT,
                structured_data=f"[{Subject.ENDPOINT_PATHS[0]} Verb POST]")
            return create_response(message={'error': "internal server error"}, status_code=STATUS_CODES["internal_error"])

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin'])
    def delete(self, materia) -> Response:
        """
        Delete a subject.
        The request must include the subject name as a path variable.
        """

        # Check that the specified subject exists
        subject: Dict[str, Any] = fetchone_query('SELECT materia FROM materie WHERE materia = %s', (materia,)) # Only fetch the province to check existence (could be any field)
        if subject is None:
            return create_response(message={'error': 'specified subject does not exist'}, status_code=STATUS_CODES["not_found"])

        # Check if subject exists
        subject: Dict[str, Any] = fetchone_query('SELECT * FROM materie WHERE materia = %s', (materia,))
        if subject is None:
            return create_response(message={'outcome': 'error, specified subject does not exist'}, status_code=STATUS_CODES["not_found"])

        # Delete the subject
        execute_query('DELETE FROM materie WHERE materia = %s', (materia,))

        # Log the deletion
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} deleted subject {materia}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT,
            structured_data=f"[{Subject.ENDPOINT_PATHS[0]} Verb DELETE]")

        # Return a success message
        return create_response(message={'outcome': 'subject successfully deleted'}, status_code=STATUS_CODES["no_content"])

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin'])
    def patch(self, materia) -> Response:
        """
        Update a subject.
        The request must include the subject name as a path variable.
        """

        # Validate request
        data: Union[str, Dict[str, Any]] = has_valid_json(request)
        if isinstance(data, str): 
            return create_response(message={'error': data}, status_code=STATUS_CODES["bad_request"])

        # Check for sql injection
        if not is_input_safe(data):
            return create_response(message={'error': 'invalid input, suspected sql injection'}, status_code=STATUS_CODES["bad_request"])

        # Check that specified subject exists
        subject: Dict[str, Any] = fetchone_query('SELECT * FROM materie WHERE materia = %s', (materia,))
        if subject is None:
            return create_response(message={'outcome': 'error, specified subject does not exist'}, status_code=STATUS_CODES["not_found"])

        # Check that the specified fields actually exist in the database
        modifiable_columns: List[str] = ['materia', 'descrizione', 'hexColor']
        toModify: List[str]  = list(data.keys())
        error_columns: List[str] = [field for field in toModify if field not in modifiable_columns]
        if error_columns:
            return create_response(message={'outcome': f'error, field(s) {error_columns} do not exist or cannot be modified'}, status_code=STATUS_CODES["bad_request"])

        # Build the query
        query, params = build_update_query_from_filters(data=data, table_name='materie', 
                                                        id_column='materia', id_value=materia)

        # Update the subject
        execute_query(query, params)

        # Log the update
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} updated subject {materia}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT,
            structured_data=f"[{Subject.ENDPOINT_PATHS[0]} Verb PATCH]")

        # Return a success message
        return create_response(message={'outcome': 'subject successfully updated'}, status_code=STATUS_CODES["ok"])

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor', 'teacher'])
    def get(self, materia) -> Response: # TODO rework this endpoint
        """
        Get all subjects with pagination.
        The request can include limit and offset as query parameters.
        """
        
        # Gather parameters
        descrizione = request.args.get('descrizione')
        hexColor = request.args.get('hexColor')
        try:
            limit = int(request.args.get('limit', 10))  # Default limit to 10 if not provided
            offset = int(request.args.get('offset', 0))  # Default offset to 0 if not provided
        except (ValueError, TypeError):
            return create_response(message={'error': 'invalid limit or offset parameter'}, status_code=STATUS_CODES["bad_request"])

        # Build the filters dictionary (only include non-null values)
        data = {key: value for key, value in {
            'materia': materia,  # Use the path variable 'materia'
            'descrizione': descrizione,
            'hexColor': hexColor
        }.items() if value}

        try:
            # Build the query
            query, params = build_select_query_from_filters(data=data, table_name='materie', limit=limit, offset=offset)

            # Execute query
            subjects = fetchall_query(query, params)

            # Get the ids to log
            ids = [subject['materia'] for subject in subjects]

            # Log the read
            log(type='info', 
                message=f'User {get_jwt_identity().get("email")} read subjects {ids}', 
                origin_name=API_SERVER_NAME_IN_LOG, 
                origin_host=API_SERVER_HOST, 
                origin_port=API_SERVER_PORT,
                structured_data=f"[{Subject.ENDPOINT_PATHS[0]} Verb GET]")

            # Return the subjects
            return create_response(message=subjects, status_code=STATUS_CODES["ok"])
        except Exception as err:
            return create_response(message={'error': str(err)}, status_code=STATUS_CODES["internal_error"])

    @jwt_required_endpoint
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

api.add_resource(Subject, *Subject.ENDPOINT_PATHS)
