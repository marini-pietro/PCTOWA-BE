from os.path import basename as os_path_basename
from flask import Blueprint, request
from flask_restful import Api, Resource
from flask_jwt_extended import get_jwt_identity
from config import API_SERVER_HOST, API_SERVER_PORT, API_SERVER_NAME_IN_LOG, STATUS_CODES
from mysql.connector import IntegrityError
from .blueprints_utils import (check_authorization, validate_filters, 
                               fetchone_query, fetchall_query, 
                               execute_query, log, 
                               jwt_required_endpoint, create_response, 
                               build_update_query_from_filters, build_select_query_from_filters)

# Define constants
BP_NAME = os_path_basename(__file__).replace('_bp.py', '')

# Create the blueprint and API
student_bp = Blueprint(BP_NAME, __name__)
api = Api(student_bp)

class Student(Resource):
    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor'])
    def post(self, matricola):
        # Gather parameters
        nome = request.args.get('nome')
        cognome = request.args.get('cognome')
        try:
            idClasse = int(request.args.get('idClasse'))
        except (ValueError, TypeError):
            return create_response(message={'error': 'invalid idClasse parameter'}, status_code=STATUS_CODES["bad_request"])

        try:
            # Insert the student
            lastrowid = execute_query('INSERT INTO studenti VALUES (%s, %s, %s, %s)', (matricola, nome, cognome, idClasse))
            
        except IntegrityError:
            log(type='error',
                message=f'User {get_jwt_identity().get("email")} tried to create student {matricola} but it already existed',
                origin_name=API_SERVER_NAME_IN_LOG, 
                origin_host=API_SERVER_HOST, 
                origin_port=API_SERVER_PORT)
            return create_response(message={'outcome': 'error, student with provided matricola already exists'}, status_code=STATUS_CODES["bad_request"])
        except Exception as ex:
            log(type='error',
                message=f'User {get_jwt_identity().get("email")} failed to create student {matricola} with error: {str(ex)}',
                origin_name=API_SERVER_NAME_IN_LOG, 
                origin_host=API_SERVER_HOST, 
                origin_port=API_SERVER_PORT)
            return create_response(message={'error': "internal server error"}, status_code=STATUS_CODES["internal_error"])

        # Log the student creation
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} created student {matricola}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        return create_response(message={"outcome": "student successfully created",
                                        'location': f'http://{API_SERVER_HOST}:{API_SERVER_PORT}/api/{BP_NAME}/{lastrowid}'}, status_code=STATUS_CODES["created"])

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor'])
    def delete(self, matricola):
        # Delete the student
        execute_query('DELETE FROM studenti WHERE matricola = %s', (matricola,))

        # Log the deletion
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} deleted student {matricola}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        # Return a success message
        return create_response(message={'outcome': 'student successfully deleted'}, status_code=STATUS_CODES["no_content"])

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor'])
    def patch(self, matricola):
        # Gather parameters
        toModify: list[str] = request.args.get('toModify').split(',')  # toModify is a list of fields to modify
        newValues: list[str] = request.args.get('newValue').split(',')  # newValue is a list of values to set

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
            message=f'User {get_jwt_identity().get("email")} updated student {matricola}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        # Return a success message
        return create_response(message={'outcome': 'student successfully updated'}, status_code=STATUS_CODES["ok"])

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor', 'teacher'])
    def get(self, matricola):
        # Gather parameters
        nome = request.args.get('nome')
        cognome = request.args.get('cognome')
        try:
            idClasse = int(request.args.get('idClasse')) if request.args.get('idClasse') else None
        except (ValueError, TypeError):
            return create_response(message={'error': 'invalid idClasse parameter'}, status_code=STATUS_CODES["bad_request"])
        try:
            limit = int(request.args.get('limit', 10))  # Default limit to 10 if not provided
            offset = int(request.args.get('offset', 0))  # Default offset to 0 if not provided
        except (ValueError, TypeError):
            return create_response(message={'error': 'invalid limit or offset parameter'}, status_code=STATUS_CODES["bad_request"])

        # Build the filters dictionary (only include non-null values)
        data = {key: value for key, value in {
            'nome': nome,
            'cognome': cognome,
            'idClasse': idClasse,
            'matricola': matricola  # Use the path variable 'matricola'
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
                message=f'User {get_jwt_identity().get("email")} read students {ids}', 
                origin_name=API_SERVER_NAME_IN_LOG, 
                origin_host=API_SERVER_HOST, 
                origin_port=API_SERVER_PORT)

            # Return the results
            return create_response(message=students, status_code=STATUS_CODES["ok"])        
        except Exception as err:
            return create_response(message={'error': str(err)}, status_code=STATUS_CODES["internal_error"])

api.add_resource(Student, f'/{BP_NAME}/<int:matricola>')