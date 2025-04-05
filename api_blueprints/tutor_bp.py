from flask import Blueprint, request
from flask_restful import Api, Resource
from flask_jwt_extended import get_jwt_identity
from config import API_SERVER_HOST, API_SERVER_PORT, API_SERVER_NAME_IN_LOG, STATUS_CODES
from .blueprints_utils import (check_authorization, validate_filters, 
                               fetchone_query, fetchall_query, 
                               execute_query, log, 
                               jwt_required_endpoint, create_response, 
                               build_select_query_from_filters, build_update_query_from_filters)

# Create the blueprint and API
tutor_bp = Blueprint('tutor', __name__)
api = Api(tutor_bp)

class TutorRegister(Resource):
    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor'])
    def post(self):
        # Gather parameters
        nome = request.args.get('nome')
        cognome = request.args.get('cognome')
        telefono = request.args.get('telefono')
        email = request.args.get('email')

        # Check if tutor already exists
        tutor = fetchone_query('SELECT * FROM tutor WHERE emailTutor = %s AND telefonoTutor = %s', (email, telefono))
        if tutor is not None:
            return create_response(message={'outcome': 'error, specified tutor already exists'}, status_code=409)

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
        return create_response(message={'outcome': 'tutor successfully created'}, status_code=STATUS_CODES["created"])

class TutorDelete(Resource):
    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor'])
    def delete(self):
        # Gather parameters
        idTutor = int(request.args.get('idTutor'))

        # Delete the tutor
        execute_query('DELETE FROM tutor WHERE idTutor = %s', (idTutor,))

        # Log the deletion
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} deleted tutor', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        # Return a success message
        return create_response(message={'outcome': 'tutor successfully deleted'}, status_code=STATUS_CODES["no_content"])

class TutorUpdate(Resource):
    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor'])
    def patch(self):
        # Gather parameters
        try:
            idTutor = int(request.args.get('idTutor'))
        except (ValueError, TypeError):
            return create_response(message={'outcome': 'invalid idTutor'}, status_code=STATUS_CODES["bad_request"])
        toModify: list[str] = request.args.get('toModify').split(',')
        newValues: list[str] = request.args.get('newValue').split(',')

        # Validate parameters
        if len(toModify) != len(newValues):
            return create_response(message={'outcome': 'Mismatched fields and values lists lengths'}, status_code=STATUS_CODES["bad_request"])

        # Build a dictionary with fields as keys and values as values
        updates = dict(zip(toModify, newValues))  # {field1: value1, field2: value2, ...}

        # Check that the specified fields can be modified
        not_allowed_fields: list[str] = ['idTutor']
        for field in toModify:
            if field in not_allowed_fields:
                return create_response(message={'outcome': f'error, specified field "{field}" cannot be modified'}, status_code=STATUS_CODES["bad_request"])

        # Check that the specified fields actually exist in the database
        outcome = validate_filters(data=updates, table_name='tutor')
        if outcome is not True:  # if the validation fails, outcome will be a dict with the error message
            return create_response(message=outcome, status_code=STATUS_CODES["bad_request"])

        # Check if tutor exists
        tutor = fetchone_query('SELECT * FROM tutor WHERE idTutor = %s', (idTutor,))
        if tutor is None:
            return create_response(message={'outcome': 'error, specified tutor does not exist'}, status_code=STATUS_CODES["not_found"])

        # Build the update query
        query, params = build_update_query_from_filters(data=updates, table_name='tutor', id=idTutor)

        # Update the tutor
        execute_query(query, params)

        # Log the update
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} updated tutor with id {idTutor}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        # Return a success message
        return create_response(message={'outcome': 'tutor successfully updated'}, status_code=STATUS_CODES["ok"])

class TutorRead(Resource):
    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor', 'teacher'])
    def get(self):
        # Gather parameters
        nome = request.args.get('nome')
        cognome = request.args.get('cognome')
        emailTutor = request.args.get('emailTutor')
        telefonoTutor = request.args.get('telefonoTutor')
        try:
            idTutor = int(request.args.get('idTutor'))
        except (ValueError, TypeError):
            return create_response(message={'error': 'invalid idTutor parameter'}, status_code=STATUS_CODES["bad_request"])
        try:
            limit = int(request.args.get('limit'))
            offset = int(request.args.get('offset'))
        except (ValueError, TypeError):
            return create_response(message={'error': 'invalid limit or offset parameter'}, status_code=STATUS_CODES["bad_request"])

        # Build the filters dictionary (only include non-null values)
        data = {key: value for key, value in {
            'idTutor': idTutor,
            'nome': nome,
            'cognome': cognome,
            'emailTutor': emailTutor,
            'telefonoTutor': telefonoTutor
        }.items() if value is not None}

        try:
            # Build the query
            query, params = build_select_query_from_filters(
                data=data, 
                table_name='tutor',
                limit=limit, 
                offset=offset
            )

            # Execute query
            tutors = fetchone_query(query, params)

            # Get the ids to log
            ids = [tutor['idTutor'] for tutor in tutors]

            # Log the read
            log(type='info', 
                message=f'User {get_jwt_identity().get("email")} read tutors {ids}', 
                origin_name=API_SERVER_NAME_IN_LOG, 
                origin_host=API_SERVER_HOST, 
                origin_port=API_SERVER_PORT)

            # Return the results
            return create_response(message=tutors, status_code=STATUS_CODES["ok"])
        except Exception as err:
            return create_response(message={'error': str(err)}, status_code=STATUS_CODES["internal_error"])

# Add resources to the API
api.add_resource(TutorRegister, '/register')
api.add_resource(TutorDelete, '/delete')
api.add_resource(TutorUpdate, '/update')
api.add_resource(TutorRead, '/read')