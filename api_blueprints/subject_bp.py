from flask import Blueprint, jsonify, request
from flask_restful import Api, Resource
from config import API_SERVER_HOST, API_SERVER_PORT, API_SERVER_NAME_IN_LOG
from utils import fetchone_query, execute_query, log, jwt_required_endpoint

# Create the blueprint and API
subjects_bp = Blueprint('subjects', __name__)
api = Api(subjects_bp)

class SubjectRegister(Resource):
    @jwt_required_endpoint()
    def post(self):
        # Gather parameters
        materia = request.args.get('materia')
        descrizione = request.args.get('descrizione')

        # Check if subject exists
        subject = fetchone_query('SELECT * FROM materie WHERE materia = %s', (materia,))
        if subject is not None:
            return jsonify({'outcome': 'error, specified subject already exists'})

        # Insert the subject
        execute_query('INSERT INTO materie (materia, descr) VALUES (%s, %s)', (materia, descrizione))

        # Log the subject creation
        log(type='info', 
            message=f'User {request.user_identity} created subject {materia}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        return jsonify({'outcome': 'subject successfully created'}), 201

class SubjectDelete(Resource):
    @jwt_required_endpoint()
    def delete(self):
        # Gather parameters
        materia = request.args.get('materia')

        # Check if subject exists
        subject = fetchone_query('SELECT * FROM materie WHERE materia = %s', (materia,))
        if subject is None:
            return jsonify({'outcome': 'error, specified subject does not exist'})

        # Delete the subject
        execute_query('DELETE FROM materie WHERE materia = %s', (materia,))

        # Log the deletion
        log(type='info', 
            message=f'User {request.user_identity} deleted subject {materia}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        return jsonify({'outcome': 'subject successfully deleted'})

class SubjectUpdate(Resource):
    @jwt_required_endpoint()
    def patch(self):
        # Gather parameters
        materia = request.args.get('materia')
        toModify = request.args.get('toModify')
        newValue = request.args.get('newValue')

        # Check if the field to modify is allowed
        if toModify in ['materia']:
            return jsonify({'outcome': 'error, specified field cannot be modified'})

        # Check if subject exists
        subject = fetchone_query('SELECT * FROM materie WHERE materia = %s', (materia,))
        if subject is None:
            return jsonify({'outcome': 'error, specified subject does not exist'})

        # Update the subject
        execute_query(f'UPDATE materie SET {toModify} = %s WHERE materia = %s', (newValue, materia))

        # Log the update
        log(type='info', 
            message=f'User {request.user_identity} updated subject {materia}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        return jsonify({'outcome': 'subject successfully updated'})
    
class SubjectBind(Resource):
    @jwt_required_endpoint()
    def post(self):
        # Gather parameters
        idTurno = int(request.args.get('idTurno'))
        materia = request.args.get('materia')

        # Check if turn exists
        turn = fetchone_query('SELECT * FROM turni WHERE idTurno = %s', (idTurno,))
        if turn is None:
            return jsonify({'outcome': 'error, specified turn does not exist'})
        
        # Check if subject exists
        subject = fetchone_query('SELECT * FROM materie WHERE materia = %s', (materia,))
        if subject is None:
            return jsonify({'outcome': 'error, specified subject does not exist'})
        
        # Bind the turn to the subject
        execute_query('INSERT INTO turnoMateria (idTurno, materia) VALUES (%s, %s)', (idTurno, materia))
        
        # Log the binding
        log(type='info', 
            message=f'User {request.user_identity} binded turn {idTurno} to subject {materia}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        return jsonify({'outcome': 'success, turn binded to subject successfully'})
    
class SubjectUnbind(Resource):
    @jwt_required_endpoint()
    def delete(self):
        # Gather parameters
        idTurno = int(request.args.get('idTurno'))
        materia = request.args.get('materia')

        # Check if turn exists
        turn = fetchone_query('SELECT * FROM turni WHERE idTurno = %s', (idTurno,))
        if turn is None:
            return jsonify({'outcome': 'error, specified turn does not exist'})
        
        # Check if subject exists
        subject = fetchone_query('SELECT * FROM materie WHERE materia = %s', (materia,))
        if subject is None:
            return jsonify({'outcome': 'error, specified subject does not exist'})
        
        # Unbind the turn from the subject
        execute_query('DELETE FROM turnoMateria WHERE idTurno = %s AND materia = %s', (idTurno, materia))
        
        # Log the unbinding
        log(type='info', 
            message=f'User {request.user_identity} unbinded turn {idTurno} from subject {materia}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        return jsonify({'outcome': 'success, turn unbinded from subject successfully'})
    
class SubjectRead(Resource):
    @jwt_required_endpoint()
    def get(self):
        # Gather parameters
        materia = request.args.get('materia')

        # Check if subject exists
        subject = fetchone_query('SELECT * FROM materie WHERE materia = %s', (materia,))
        if subject is None:
            return jsonify({'outcome': 'error, specified subject does not exist'})

        # Log the read
        log(type="info",
            message=f"User {request.user_identity} read subject {materia}", 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        # Return the subject
        return jsonify({'materia': subject[0], 'descrizione': subject[1]})

# Add resources to the API
api.add_resource(SubjectRegister, '/register')
api.add_resource(SubjectDelete, '/delete')
api.add_resource(SubjectUpdate, '/update')
api.add_resource(SubjectBind, '/bind')
api.add_resource(SubjectUnbind, '/unbind')
api.add_resource(SubjectRead, '/read')
