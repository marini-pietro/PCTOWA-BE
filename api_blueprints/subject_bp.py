from os.path import basename as os_path_basename
from flask import Blueprint, request, Response
from flask_restful import Api, Resource
from flask_jwt_extended import get_jwt_identity
from config import API_SERVER_HOST, API_SERVER_PORT, API_SERVER_NAME_IN_LOG, STATUS_CODES
from re import match as re_match
from mysql.connector import IntegrityError
from .blueprints_utils import (check_authorization, validate_filters, 
                               fetchone_query, fetchall_query, 
                               execute_query, log, 
                               jwt_required_endpoint, create_response, 
                               build_update_query_from_filters, build_select_query_from_filters)

# Define constants
BP_NAME = os_path_basename(__file__).replace('_bp.py', '')

# Create the blueprint and API
subject_bp = Blueprint(BP_NAME, __name__)
api = Api(subject_bp)

class Subject(Resource):
    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin'])
    def post(self, materia) -> Response:
        """
        Create a new subject.
        The request body must be a JSON object with application/json content type.
        """
        # Ensure the request has a JSON body
        if not request.is_json or request.json is None:
            return create_response(message={'error': 'Request body must be valid JSON with Content-Type: application/json'}, status_code=STATUS_CODES["bad_request"])
        
        # Gather parameters
        descrizione = request.json.get('descrizione')
        hexColor = request.json.get('hexColor')

        # Validate parameters
        if hexColor is not None and not re_match(r'^#[0-9A-Fa-f]{6}$', hexColor):
            return create_response(message={'outcome': 'invalid hexColor format'}, status_code=STATUS_CODES["bad_request"])

        try:
            # Insert the subject
            lastrowid = execute_query('INSERT INTO materie (materia, descrizione, hexColor) VALUES (%s, %s, %s)', (materia, descrizione, hex))
        except IntegrityError:
            log(type='error',
                message=f'User {get_jwt_identity().get("email")} tried to create subject {materia} but it already existed',
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                origin_port=API_SERVER_PORT)
            return create_response(message={'outcome': 'error, specified subject already exists'}, status_code=STATUS_CODES["conflict"])
        except Exception as ex:
            log(type='error',
                message=f'User {get_jwt_identity().get("email")} failed to create subject {materia} with error: {str(ex)}',
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                origin_port=API_SERVER_PORT)
            return create_response(message={'error': "internal server error"}, status_code=STATUS_CODES["internal_error"])

        # Log the subject creation
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} created subject {materia}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        # Return a success message
        return create_response(message={'outcome': 'subject successfully created',
                                        'location': f'http://{API_SERVER_HOST}:{API_SERVER_PORT}/api/{BP_NAME}/{lastrowid}'}, status_code=STATUS_CODES["created"])

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin'])
    def delete(self, materia) -> Response:
        """
        Delete a subject.
        The request must include the subject name as a path variable.
        """
        # Check if subject exists
        subject = fetchone_query('SELECT * FROM materie WHERE materia = %s', (materia,))
        if subject is None:
            return create_response(message={'outcome': 'error, specified subject does not exist'}, status_code=STATUS_CODES["not_found"])

        # Delete the subject
        execute_query('DELETE FROM materie WHERE materia = %s', (materia,))

        # Log the deletion
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} deleted subject {materia}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        # Return a success message
        return create_response(message={'outcome': 'subject successfully deleted'}, status_code=STATUS_CODES["no_content"])

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin'])
    def patch(self, materia) -> Response:
        """
        Update a subject.
        The request must include the subject name as a path variable.
        """
        # Gather parameters
        toModify: list[str] = request.args.get('toModify').split(',')
        newValues: list[str] = request.args.get('newValue').split(',')

        # Validate parameters
        if len(toModify) != len(newValues):
            return create_response(message={'outcome': 'Mismatched fields and values lists lengths'}, status_code=STATUS_CODES["bad_request"])

        # Build a dictionary with fields as keys and values as values
        updates = dict(zip(toModify, newValues))  # {field1: value1, field2: value2, ...}

        # Check that the specified fields can be modified
        not_allowed_fields: list[str] = ['materia']
        for field in toModify:
            if field in not_allowed_fields:
                return create_response(message={'outcome': f'error, field "{field} cannot be modified"'}, status_code=STATUS_CODES["bad_request"])

        # Check that the specified fields actually exist in the database
        outcome = validate_filters(toModify, 'materie')
        if outcome is not True:
            return create_response(outcome, STATUS_CODES["bad_request"])

        # Check that specified subject exists
        subject = fetchone_query('SELECT * FROM materie WHERE materia = %s', (materia,))
        if subject is None:
            return create_response(message={'outcome': 'error, specified subject does not exist'}, status_code=STATUS_CODES["not_found"])

        # Build the query
        query, params = build_update_query_from_filters(data=updates, table_name='materie', id=materia)

        # Update the subject
        execute_query(query, params)

        # Log the update
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} updated subject {materia}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        # Return a success message
        return create_response(message={'outcome': 'subject successfully updated'}, status_code=STATUS_CODES["ok"])

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor', 'teacher'])
    def get(self, materia) -> Response:
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
                origin_port=API_SERVER_PORT)

            # Return the subjects
            return create_response(message=subjects, status_code=STATUS_CODES["ok"])
        except Exception as err:
            return create_response(message={'error': str(err)}, status_code=STATUS_CODES["internal_error"])

api.add_resource(Subject, f'/{BP_NAME}/<string:materia>')
