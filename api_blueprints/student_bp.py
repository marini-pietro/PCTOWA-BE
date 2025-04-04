from flask import Blueprint, request
from flask_restful import Api, Resource
from config import API_SERVER_HOST, API_SERVER_PORT, API_SERVER_NAME_IN_LOG, STATUS_CODES
from .blueprints_utils import (check_authorization, validate_filters, 
                               fetchone_query, fetchall_query, 
                               execute_query, log, 
                               jwt_required_endpoint, create_response, 
                               build_update_query_from_filters, build_select_query_from_filters)

# Create the blueprint and API
student_bp = Blueprint('student', __name__)
api = Api(student_bp)

class StudentRegister(Resource):
    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor'])
    def post(self):
        # Gather parameters
        nome = request.args.get('nome')
        cognome = request.args.get('cognome')
        try:
            matricola = int(request.args.get('matricola'))
        except (ValueError, TypeError):
            return create_response(message={'error': 'invalid matricola parameter'}, status_code=STATUS_CODES["bad_request"])
        try:
            idClasse = int(request.args.get('idClasse'))
        except (ValueError, TypeError):
            return create_response(message={'error': 'invalid idClasse parameter'}, status_code=STATUS_CODES["bad_request"])

        try:
            # Insert the student
            execute_query('INSERT INTO studenti VALUES (%s, %s, %s, %s)', (matricola, nome, cognome, idClasse))

            # Log the student creation
            log(type='info', 
                message=f'User {request.user_identity} created student {matricola}', 
                origin_name=API_SERVER_NAME_IN_LOG, 
                origin_host=API_SERVER_HOST, 
                origin_port=API_SERVER_PORT)

            return create_response(message={"outcome": "student successfully created"}, status_code=STATUS_CODES["created"])
        except Exception as err:
            return create_response(message={'outcome': 'error, student with provided matricola already exists'}, status_code=STATUS_CODES["bad_request"])

class StudentDelete(Resource):
    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor'])
    def delete(self):
        # Gather parameters
        try:
            matricola = int(request.args.get('matricola'))
        except (ValueError, TypeError):
            return create_response(message={'error': 'invalid matricola parameter'}, status_code=STATUS_CODES["bad_request"])

        # Delete the student
        execute_query('DELETE FROM studenti WHERE matricola = %s', (matricola,))

        # Log the deletion
        log(type='info', 
            message=f'User {request.user_identity} deleted student {matricola}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        # Return a success message
        return create_response(message={'outcome': 'student successfully deleted'}, status_code=STATUS_CODES["no_content"])

class StudentUpdate(Resource):
    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor'])
    def patch(self):
        # Gather parameters
        toModify: list[str] = request.args.get('toModify').split(',')  # toModify is a list of fields to modify
        newValues: list[str] = request.args.get('newValue').split(',')  # newValue is a list of values to set
        try:
            matricola = int(request.args.get('matricola'))
        except (ValueError, TypeError):
            return create_response(message={'error': 'invalid matricola parameter'}, status_code=STATUS_CODES["bad_request"])

        # Validate parameters
        if len(toModify) != len(newValues):
            return create_response(message={'outcome': 'Mismatched fields and values lists lengths'}, status_code=STATUS_CODES["bad_request"])

        # Build a dictionary with fields as keys and values as values
        updates = dict(zip(toModify, newValues))  # {field1: value1, field2: value2, ...}

        # Check that the specified fields can be modified
        not_allowed_fields: list[str] = ['matricola']
        for field in toModify:
            if field in not_allowed_fields:
                return create_response(message={'outcome': f'error, field "{field} cannot be modified"'}, status_code=STATUS_CODES["bad_request"])
            
        # Check that the specified fields actually exist in the database
        outcome = validate_filters(data=updates, table_name='studenti')
        if outcome is not True:  # if the validation fails, outcome will be a dict with the error message
            return create_response(message=outcome, status_code=STATUS_CODES["bad_request"])
        
        # Check that the specified student exists
        student = fetchone_query('SELECT * FROM studenti WHERE matricola = %s', (matricola,))
        if student is None:
            return create_response(message={'outcome': 'error, specified student does not exist'}, status_code=STATUS_CODES["not_found"])

        # Build the update query
        query, params = build_update_query_from_filters(data=updates, table_name='studenti', id=matricola)

        # Update the student
        execute_query(query, params)

        # Log the update
        log(type='info', 
            message=f'User {request.user_identity} updated student {matricola}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        # Return a success message
        return create_response(message={'outcome': 'student successfully updated'}, status_code=STATUS_CODES["ok"])

class StudentRead(Resource):
    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor', 'teacher'])
    def get(self):
        # Gather parameters
        nome = request.args.get('nome')
        cognome = request.args.get('cognome')
        try:
            idClasse = int(request.args.get('idClasse'))
        except (ValueError, TypeError):
            return create_response(message={'error': 'invalid idClasse parameter'}, status_code=STATUS_CODES["bad_request"])
        try:
            matricola = int(request.args.get('matricola'))
        except (ValueError, TypeError):
            return create_response(message={'error': 'invalid matricola parameter'}, status_code=STATUS_CODES["bad_request"])
        try:
            limit = int(request.args.get('limit'))
            offset = int(request.args.get('offset'))
        except (ValueError, TypeError):
            return create_response(message={'error': 'invalid limit or offset parameter'}, status_code=STATUS_CODES["bad_request"])

        # Build the filters dictionary (only include non-null values)
        data = {key: value for key, value in {
            'nome': nome,
            'cognome': cognome,
            'idClasse': idClasse,
            'matricola': matricola
        }.items() if value}

        try:
            # Build the query
            query, params = build_select_query_from_filters(
                data=data, 
                table_name='studenti',
                limit=limit, 
                offset=offset
            )

            # Execute query
            students = fetchall_query(query, params)

            # Get the ids to log
            ids = [student['matricola'] for student in students]

            # Log the read
            log(type='info', 
                message=f'User {request.user_identity} read students {ids}', 
                origin_name=API_SERVER_NAME_IN_LOG, 
                origin_host=API_SERVER_HOST, 
                origin_port=API_SERVER_PORT)

            # Return the results
            return create_response(message=students, status_code=STATUS_CODES["ok"])        
        except Exception as err:
            return create_response(message={'error': str(err)}, status_code=STATUS_CODES["internal_error"])

# Add resources to the API
api.add_resource(StudentRegister, '/register')
api.add_resource(StudentDelete, '/delete')
api.add_resource(StudentUpdate, '/update')
api.add_resource(StudentRead, '/read')