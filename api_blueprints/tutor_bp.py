from flask import Blueprint, jsonify, request
from flask_restful import Api, Resource
import mysql.connector
from utils import fetchone_query, execute_query, log, jwt_required_endpoint

# Create the blueprint and API
tutor_bp = Blueprint('tutor', __name__)
api = Api(tutor_bp)

class TutorRegister(Resource):
    @jwt_required_endpoint()
    def post(self):
        # Gather parameters
        nome = request.args.get('nome')
        cognome = request.args.get('cognome')
        telefono = request.args.get('telefono')
        email = request.args.get('email')

        # Check if tutor already exists
        tutor = fetchone_query('SELECT * FROM tutor WHERE emailTutor = %s AND telefonoTutor = %s', (email, telefono))
        if tutor is not None:
            return jsonify({'outcome': 'error, specified tutor already exists'})

        # Insert the tutor
        execute_query(
            'INSERT INTO tutor (nome, cognome, telefonoTutor, emailTutor) VALUES (%s, %s, %s, %s)',
            (nome, cognome, telefono, email)
        )

        # Log the tutor creation
        log('info', f'User {request.user_identity} created a tutor')

        return jsonify({'outcome': 'tutor successfully created'}), 201

class TutorDelete(Resource):
    @jwt_required_endpoint()
    def delete(self):
        # Gather parameters
        idTutor = int(request.args.get('idTutor'))

        # Check if tutor exists
        tutor = fetchone_query('SELECT * FROM tutor WHERE idTutor = %s', (idTutor,))
        if tutor is None:
            return jsonify({'outcome': 'error, specified tutor does not exist'})

        # Delete the tutor
        execute_query('DELETE FROM tutor WHERE idTutor = %s', (idTutor,))

        # Log the deletion
        log('info', f'User {request.user_identity} deleted tutor')

        return jsonify({'outcome': 'tutor successfully deleted'})

class TutorUpdate(Resource):
    @jwt_required_endpoint()
    def patch(self):
        # Gather parameters
        idTutor = int(request.args.get('idTutor'))
        toModify = request.args.get('toModify')
        newValue = request.args.get('newValue')

        # Check if the field to modify is allowed
        if toModify in ['idTutor']:
            return jsonify({'outcome': 'error, specified field cannot be modified'})

        # Check if tutor exists
        tutor = fetchone_query('SELECT * FROM tutor WHERE idTutor = %s', (idTutor,))
        if tutor is None:
            return jsonify({'outcome': 'error, specified tutor does not exist'})

        # Update the tutor
        execute_query(f'UPDATE tutor SET {toModify} = %s WHERE idTutor = %s', (newValue, idTutor))

        # Log the update
        log('info', f'User {request.user_identity} updated tutor with id {idTutor}')

        return jsonify({'outcome': 'tutor successfully updated'})

class TutorRead(Resource):
    @jwt_required_endpoint()
    def get(self):
        # Gather parameters
        try:
            idTutor = int(request.args.get('idTutor'))
        except (ValueError, TypeError):
            return jsonify({'error': 'invalid idTutor parameter'}), 400

        # Execute query
        try:
            tutor = fetchone_query('SELECT * FROM tutor WHERE idTutor = %s', (idTutor,))

            # Log the read
            log('info', f'User {request.user_identity} read tutor with id {idTutor}')

            return jsonify(tutor), 200
        except mysql.connector.Error as err:
            return jsonify({'error': str(err)}), 500

# Add resources to the API
api.add_resource(TutorRegister, '/register')
api.add_resource(TutorDelete, '/delete')
api.add_resource(TutorUpdate, '/update')
api.add_resource(TutorRead, '/read')