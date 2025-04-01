from flask import Blueprint, request
from flask_restful import Api, Resource
import mysql.connector
from config import API_SERVER_HOST, API_SERVER_PORT, API_SERVER_NAME_IN_LOG, STATUS_CODES
from .blueprints_utils import validate_filters, validate_inputs, build_query_from_filters, fetchone_query, fetchall_query, execute_query, log, jwt_required_endpoint, create_response

# Create the blueprint and API
student_bp = Blueprint('student', __name__)
api = Api(student_bp)

class StudentRegister(Resource):
    @jwt_required_endpoint
    def post(self):
        # Gather parameters
        matricola = request.args.get('matricola')
        nome = request.args.get('nome')
        cognome = request.args.get('cognome')
        idClasse = request.args.get('idClasse')

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
        except mysql.connector.IntegrityError:
            return create_response(message={'outcome': 'error, student with provided matricola already exists'}, status_code=STATUS_CODES["bad_request"])

class StudentDelete(Resource):
    @jwt_required_endpoint
    def delete(self):
        # Gather parameters
        matricola = request.args.get('matricola')

        # Check if student exists
        student = fetchone_query('SELECT * FROM studenti WHERE matricola = %s', (matricola,))
        if student is None:
            return {'outcome': 'error, specified student does not exist'}, STATUS_CODES["not_found"]

        # Delete the student
        execute_query('DELETE FROM studenti WHERE matricola = %s', (matricola,))

        # Log the deletion
        log(type='info', 
            message=f'User {request.user_identity} deleted student {matricola}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        return create_response(message={'outcome': 'student successfully deleted'}, status_code=STATUS_CODES["ok"])

class StudentUpdate(Resource):
    @jwt_required_endpoint
    def patch(self):
        # Gather parameters
        matricola = request.args.get('matricola')
        toModify = request.args.get('toModify')
        newValue = request.args.get('newValue')

        # Check if the field to modify is allowed
        if toModify in ['matricola']:
            return create_response(message={'outcome': 'error, specified field cannot be modified'}, status_code=STATUS_CODES["bad_request"])

        # Check if student exists
        student = fetchone_query('SELECT * FROM studenti WHERE matricola = %s', (matricola,))
        if student is None:
            return create_response(message={'outcome': 'error, specified student does not exist'}, status_code=STATUS_CODES["not_found"])

        # Update the student
        execute_query(f'UPDATE studenti SET {toModify} = %s WHERE matricola = %s', (newValue, matricola))

        # Log the update
        log(type='info', 
            message=f'User {request.user_identity} updated student {matricola}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        return create_response(message={'outcome': 'student successfully updated'}, status_code=STATUS_CODES["ok"])

class StudentRead(Resource):
    @jwt_required_endpoint
    def get(self):
        # Gather URL parameters
        try:
            limit = int(request.args.get('limit'))
            offset = int(request.args.get('offset'))
        except (ValueError, TypeError):
            return create_response(message={'error': 'invalid limit or offset parameter'}, status_code=STATUS_CODES["bad_request"])

        # Gather json filters
        data = request.get_json()

        # Validate filters
        outcome = validate_filters(data=data, table_name='studenti')
        if outcome != True:  # if the validation fails, outcome will be a dict with the error message
            return create_response(message=outcome, status_code=STATUS_CODES["bad_request"])

        try:
            # Build the query
            query, params = build_query_from_filters(data=data, table_name='studenti', limit=limit, offset=offset)

            # Execute query
            students = fetchall_query(query, tuple(params))

            # Log the read
            log(type='info', 
                message=f'User {request.user_identity} read students with filters {data}', 
                origin_name=API_SERVER_NAME_IN_LOG, 
                origin_host=API_SERVER_HOST, 
                origin_port=API_SERVER_PORT)

            return create_response(message=students, status_code=STATUS_CODES["ok"])
        
        except Exception as err:
            return create_response(message={'error': str(err)}, status_code=STATUS_CODES["internal_error"])

class StudentBindTurn(Resource):
    @jwt_required_endpoint
    def post(self):
        # Gather parameters
        idTurno = int(request.args.get('idTurno'))
        matricola = request.args.get('matricola')

        # Check if turn exists
        turn = fetchone_query('SELECT * FROM turni WHERE idTurno = %s', (idTurno,))
        if turn is None:
            return create_response(message={'outcome': 'error, specified turn does not exist'}, status_code=STATUS_CODES["not_found"])
        
        # Check if student exists
        student = fetchone_query('SELECT * FROM studenti WHERE matricola = %s', (matricola,))
        if student is None:
            return create_response(message={'outcome': 'error, specified student does not exist'}, status_code=STATUS_CODES["not_found"])
        
        # Check if student is already bound to the turn
        binding = fetchone_query('SELECT * FROM studenti_turni WHERE idTurno = %s AND matricola = %s', (idTurno, matricola))
        if binding is not None:
            return create_response(message={'outcome': 'error, student is already bound to the turn'}, status_code=STATUS_CODES["bad_request"])
        
        # Bind the student to the turn
        execute_query('INSERT INTO studenti_turni VALUES (%s, %s)', (matricola, idTurno))

        # Log the bind
        log(type="info", 
            message=f"User {request.user_identity} binded student {matricola} to turn {idTurno}", 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)
        
        return create_response(message={'outcome': 'student successfully bound to the turn'}, status_code=STATUS_CODES["created"])

# Add resources to the API
api.add_resource(StudentRegister, '/register')
api.add_resource(StudentDelete, '/delete')
api.add_resource(StudentUpdate, '/update')
api.add_resource(StudentRead, '/read')
api.add_resource(StudentBindTurn, '/bind_turn')