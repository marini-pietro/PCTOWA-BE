from flask import Blueprint, request, make_response, jsonify
from flask_restful import Api, Resource
from config import API_SERVER_HOST, API_SERVER_PORT, API_SERVER_NAME_IN_LOG
from .blueprints_utils import validate_filters, build_query_from_filters, fetchone_query, fetchall_query, execute_query, log, jwt_required_endpoint

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
            return make_response(jsonify({'outcome': 'error, specified tutor already exists'}), 409)

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

        return make_response(jsonify({'outcome': 'tutor successfully created'}), 201)

class TutorDelete(Resource):
    @jwt_required_endpoint
    def delete(self):
        # Gather parameters
        idTutor = int(request.args.get('idTutor'))

        # Check if tutor exists
        tutor = fetchone_query('SELECT * FROM tutor WHERE idTutor = %s', (idTutor,))
        if tutor is None:
            return make_response(jsonify({'outcome': 'error, specified tutor does not exist'}), 404)

        # Delete the tutor
        execute_query('DELETE FROM tutor WHERE idTutor = %s', (idTutor,))

        # Log the deletion
        log(type='info', 
            message=f'User {request.user_identity} deleted tutor', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        return make_response(jsonify({'outcome': 'tutor successfully deleted'}), 200)

class TutorUpdate(Resource):
    @jwt_required_endpoint
    def patch(self):
        # Gather parameters
        idTutor = int(request.args.get('idTutor'))
        toModify = request.args.get('toModify')
        newValue = request.args.get('newValue')

        # Check if the field to modify is allowed
        if toModify in ['idTutor']:
            return make_response(jsonify({'outcome': 'error, specified field cannot be modified'}), 400)

        # Check if tutor exists
        tutor = fetchone_query('SELECT * FROM tutor WHERE idTutor = %s', (idTutor,))
        if tutor is None:
            return make_response(jsonify({'outcome': 'error, specified tutor does not exist'}), 404)

        # Update the tutor
        execute_query(f'UPDATE tutor SET {toModify} = %s WHERE idTutor = %s', (newValue, idTutor))

        # Log the update
        log(type='info', 
            message=f'User {request.user_identity} updated tutor with id {idTutor}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        return make_response(jsonify({'outcome': 'tutor successfully updated'}), 200)

class TutorRead(Resource):
    @jwt_required_endpoint
    def get(self):
        # Gather URL parameters
        try:
            limit = int(request.args.get('limit'))
            offset = int(request.args.get('offset'))
        except (ValueError, TypeError):
            return make_response(jsonify({'error': 'invalid limit or offset parameter'}), 400)

        # Gather json filters
        data = request.get_json()

        # Validate filters
        outcome = validate_filters(data=data, table_name='tutor')
        if outcome != True:  # if the validation fails, outcome will be a dict with the error message
            return make_response(jsonify(outcome), 400)

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

            return make_response(jsonify(tutors), 200)
        except Exception as err:
            return make_response(jsonify({'error': str(err)}), 500)

# Add resources to the API
api.add_resource(TutorRegister, '/register')
api.add_resource(TutorDelete, '/delete')
api.add_resource(TutorUpdate, '/update')
api.add_resource(TutorRead, '/read')