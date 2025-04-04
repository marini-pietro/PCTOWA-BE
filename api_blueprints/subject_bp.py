from flask import Blueprint, request
from flask_restful import Api, Resource
from config import API_SERVER_HOST, API_SERVER_PORT, API_SERVER_NAME_IN_LOG, STATUS_CODES
from .blueprints_utils import (check_authorization, validate_filters, 
                               fetchone_query, fetchall_query, 
                               execute_query, log, 
                               jwt_required_endpoint, create_response, 
                               build_update_query_from_filters, build_select_query_from_filters)
import re

# Create the blueprint and API
subject_bp = Blueprint('subjects', __name__)
api = Api(subject_bp)

class SubjectRegister(Resource):
    @jwt_required_endpoint
    def post(self):
        # Gather parameters
        materia = request.args.get('materia')
        descrizione = request.args.get('descrizione')
        hexColor = request.args.get('hexColor')

        # Validate parameters
        if hexColor is not None and not re.match(r'^#[0-9A-Fa-f]{6}$', hexColor):
            return create_response(message={'outcome': 'invalid hexColor format'}, status_code=STATUS_CODES["bad_request"])

        # Check if subject already exists
        subject = fetchone_query('SELECT * FROM materie WHERE materia = %s', (materia,))
        if subject is not None:
            return create_response(message={'outcome': 'error, specified subject already exists'}, status_code=STATUS_CODES["bad_request"])

        # Insert the subject
        execute_query('INSERT INTO materie (materia, descr) VALUES (%s, %s)', (materia, descrizione))

        # Log the subject creation
        log(type='info', 
            message=f'User {request.user_identity} created subject {materia}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        # Return a success message
        return create_response(message={'outcome': 'subject successfully created'}, status_code=STATUS_CODES["created"])

class SubjectDelete(Resource):
    @jwt_required_endpoint
    def delete(self):
        # Gather parameters
        materia = request.args.get('materia')

        # Validate parameters
        if not materia:
            return create_response(message={'outcome': 'missing subject name'}, status_code=STATUS_CODES["bad_request"])

        # Check if subject exists
        subject = fetchone_query('SELECT * FROM materie WHERE materia = %s', (materia,))
        if subject is None:
            return create_response(message={'outcome': 'error, specified subject does not exist'}, status_code=STATUS_CODES["not_found"])

        # Delete the subject
        execute_query('DELETE FROM materie WHERE materia = %s', (materia,))

        # Log the deletion
        log(type='info', 
            message=f'User {request.user_identity} deleted subject {materia}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        # Return a success message
        return create_response(message={'outcome': 'subject successfully deleted'}, status_code=STATUS_CODES["no_content"])

class SubjectUpdate(Resource):
    @jwt_required_endpoint
    def patch(self):
        # Gather parameters
        materia = request.args.get('materia')
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
            message=f'User {request.user_identity} updated subject {materia}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        # Return a success message
        return create_response(message={'outcome': 'subject successfully updated'}, status_code=STATUS_CODES["ok"])
    
class SubjectRead(Resource):
    @jwt_required_endpoint
    def get(self):
        # Gather parameters
        materia = request.args.get('materia')
        descrizione = request.args.get('descrizione')
        hexColor = request.args.get('hexColor')
        try:
            limit = int(request.args.get('limit'))
            offset = int(request.args.get('offset'))
        except (ValueError, TypeError):
            return create_response(message={'error': 'invalid limit or offset parameter'}, status_code=STATUS_CODES["bad_request"])

        # Build the filters dictionary (only include non-null values)
        data = {key: value for key, value in {
            'materia': materia,
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
                message=f'User {request.user_identity} read subjects {ids}', 
                origin_name=API_SERVER_NAME_IN_LOG, 
                origin_host=API_SERVER_HOST, 
                origin_port=API_SERVER_PORT)

            # Return the subjects
            return create_response(message=subjects, status_code=STATUS_CODES["ok"])
        except Exception as err:
            return create_response(message={'error': str(err)}, status_code=STATUS_CODES["internal_error"])

# Add resources to the API
api.add_resource(SubjectRegister, '/register')
api.add_resource(SubjectDelete, '/delete')
api.add_resource(SubjectUpdate, '/update')
api.add_resource(SubjectRead, '/read')
