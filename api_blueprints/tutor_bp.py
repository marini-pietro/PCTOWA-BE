from flask import Blueprint, request
from flask_restful import Api, Resource
from config import API_SERVER_HOST, API_SERVER_PORT, API_SERVER_NAME_IN_LOG, STATUS_CODES
from .blueprints_utils import validate_filters, validate_inputs, build_query_from_filters, fetchone_query, fetchall_query, execute_query, log, jwt_required_endpoint, create_response

# Create the blueprint and API
tutor_bp = Blueprint('tutor', __name__)
api = Api(tutor_bp)

class TutorRegister(Resource):
    @jwt_required_endpoint
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
        execute_query(
            'INSERT INTO tutor (nome, cognome, telefonoTutor, emailTutor) VALUES (%s, %s, %s, %s)',
            (nome, cognome, telefono, email)
        )

        # Log the tutor creation
        log(type='info', 
            message=f'User {request.user_identity} created a tutor', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        return create_response(message={'outcome': 'tutor successfully created'}, status_code=STATUS_CODES["created"])

class TutorDelete(Resource):
    @jwt_required_endpoint
    def delete(self):
        # Gather parameters
        idTutor = int(request.args.get('idTutor'))

        # Check if tutor exists
        tutor = fetchone_query('SELECT * FROM tutor WHERE idTutor = %s', (idTutor,))
        if tutor is None:
            return create_response(message={'outcome': 'error, specified tutor does not exist'}, status_code=STATUS_CODES["not_found"])

        # Delete the tutor
        execute_query('DELETE FROM tutor WHERE idTutor = %s', (idTutor,))

        # Log the deletion
        log(type='info', 
            message=f'User {request.user_identity} deleted tutor', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        return create_response(message={'outcome': 'tutor successfully deleted'}, status_code=STATUS_CODES["ok"])

class TutorUpdate(Resource):
    @jwt_required_endpoint
    def patch(self):
        # Gather parameters
        idTutor = int(request.args.get('idTutor'))
        toModify = request.args.get('toModify')
        newValue = request.args.get('newValue')

        # Check if the field to modify is allowed
        if toModify in ['idTutor']:
            return create_response(message={'outcome': 'error, specified field cannot be modified'}, status_code=STATUS_CODES["bad_request"])

        # Check if tutor exists
        tutor = fetchone_query('SELECT * FROM tutor WHERE idTutor = %s', (idTutor,))
        if tutor is None:
            return create_response(message={'outcome': 'error, specified tutor does not exist'}, status_code=STATUS_CODES["not_found"])

        # Update the tutor
        execute_query(f'UPDATE tutor SET {toModify} = %s WHERE idTutor = %s', (newValue, idTutor))

        # Log the update
        log(type='info', 
            message=f'User {request.user_identity} updated tutor with id {idTutor}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        return create_response(message={'outcome': 'tutor successfully updated'}, status_code=STATUS_CODES["ok"])

class TutorRead(Resource):
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
        outcome = validate_filters(data=data, table_name='tutor')
        if outcome != True:  # if the validation fails, outcome will be a dict with the error message
            return create_response(message=outcome, status_code=STATUS_CODES["bad_request"])

        try:
            # Build the query
            query, params = build_query_from_filters(data=data, table_name='tutor', limit=limit, offset=offset)

            # Execute query
            tutors = fetchone_query(query, tuple(params))

            # Log the read
            log(type='info', 
                message=f'User {request.user_identity} read tutors with filters: {data}', 
                origin_name=API_SERVER_NAME_IN_LOG, 
                origin_host=API_SERVER_HOST, 
                origin_port=API_SERVER_PORT)

            return create_response(message=tutors, status_code=STATUS_CODES["ok"])
        except Exception as err:
            return create_response(message={'error': str(err)}, status_code=STATUS_CODES["internal_error"])

# Add resources to the API
api.add_resource(TutorRegister, '/register')
api.add_resource(TutorDelete, '/delete')
api.add_resource(TutorUpdate, '/update')
api.add_resource(TutorRead, '/read')