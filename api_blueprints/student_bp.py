from flask import Blueprint, jsonify, request
from flask_restful import Api, Resource
import mysql.connector
from config import API_SERVER_HOST, API_SERVER_PORT, API_SERVER_NAME_IN_LOG
from utils import fetchone_query, execute_query, log, jwt_required_endpoint

# Create the blueprint and API
student_bp = Blueprint('student', __name__)
api = Api(student_bp)

class StudentRegister(Resource):
    @jwt_required_endpoint()
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

            return jsonify({"outcome": "student successfully created"}), 201
        except mysql.connector.IntegrityError:
            return jsonify({'outcome': 'error, student with provided matricola already exists'}), 400

class StudentDelete(Resource):
    @jwt_required_endpoint()
    def delete(self):
        # Gather parameters
        matricola = request.args.get('matricola')

        # Check if student exists
        student = fetchone_query('SELECT * FROM studenti WHERE matricola = %s', (matricola,))
        if student is None:
            return jsonify({'outcome': 'error, specified student does not exist'})

        # Delete the student
        execute_query('DELETE FROM studenti WHERE matricola = %s', (matricola,))

        # Log the deletion
        log(type='info', 
            message=f'User {request.user_identity} deleted student {matricola}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        return jsonify({'outcome': 'student successfully deleted'})

class StudentUpdate(Resource):
    @jwt_required_endpoint()
    def patch(self):
        # Gather parameters
        matricola = request.args.get('matricola')
        toModify = request.args.get('toModify')
        newValue = request.args.get('newValue')

        # Check if the field to modify is allowed
        if toModify in ['matricola']:
            return jsonify({'outcome': 'error, specified field cannot be modified'})

        # Check if student exists
        student = fetchone_query('SELECT * FROM studenti WHERE matricola = %s', (matricola,))
        if student is None:
            return jsonify({'outcome': 'error, specified student does not exist'})

        # Update the student
        execute_query(f'UPDATE studenti SET {toModify} = %s WHERE matricola = %s', (newValue, matricola))

        # Log the update
        log(type='info', 
            message=f'User {request.user_identity} updated student {matricola}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        return jsonify({'outcome': 'student successfully updated'})

class StudentRead(Resource):
    @jwt_required_endpoint()
    def get(self):
        # Gather parameters
        try:
            matricola = int(request.args.get('matricola'))
        except (ValueError, TypeError):
            return jsonify({'error': 'invalid matricola parameter'}), 400

        # Check if student exists
        student = fetchone_query('SELECT * FROM studenti WHERE matricola = %s', (matricola,))
        if student is None:
            return jsonify({'outcome': 'error, specified student does not exist'})

        # Log the read
        log(type='info', 
            message=f'User {request.user_identity} read student {matricola}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        return jsonify(student), 200

class StudentBindTurn(Resource):
    @jwt_required_endpoint()
    def post(self):
        # Gather parameters
        idTurno = int(request.args.get('idTurno'))
        matricola = request.args.get('matricola')

        # Check if turn exists
        turn = fetchone_query('SELECT * FROM turni WHERE idTurno = %s', (idTurno,))
        if turn is None:
            return {'outcome': 'error, specified turn does not exist'}
        
        # Check if student exists
        student = fetchone_query('SELECT * FROM studenti WHERE matricola = %s', (matricola,))
        if student is None:
            return {'outcome': 'error, specified student does not exist'}
        
        # Check if student is already bound to the turn
        binding = fetchone_query('SELECT * FROM studenti_turni WHERE idTurno = %s AND matricola = %s', (idTurno, matricola))
        if binding is not None:
            return {'outcome': 'error, student is already bound to the turn'}
        
        # Bind the student to the turn
        execute_query('INSERT INTO studenti_turni VALUES (%s, %s)', (matricola, idTurno))

        # Log the bind
        log(type="info", 
            message=f"User {request.user_identity} binded student {matricola} to turn {idTurno}", 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)
        
        return {'outcome': 'student successfully bound to the turn'}

# Add resources to the API
api.add_resource(StudentRegister, '/register')
api.add_resource(StudentDelete, '/delete')
api.add_resource(StudentUpdate, '/update')
api.add_resource(StudentRead, '/read')
api.add_resource(StudentBindTurn, '/bind_turn')