from flask import Blueprint, request
from flask_restful import Api, Resource
from config import API_SERVER_HOST, API_SERVER_PORT, API_SERVER_NAME_IN_LOG, STATUS_CODES
from .blueprints_utils import validate_filters, validate_inputs, build_query_from_filters, fetchone_query, fetchall_query, execute_query, log, jwt_required_endpoint, create_response

# Create the blueprint and API
subject_bp = Blueprint('subjects', __name__)
api = Api(subject_bp)

class SubjectRegister(Resource):
    @jwt_required_endpoint
    def post(self):
        # Gather parameters
        materia = request.args.get('materia')
        descrizione = request.args.get('descrizione')

        # Check if subject exists
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

        return create_response(message={'outcome': 'subject successfully created'}, status_code=STATUS_CODES["created"])

class SubjectDelete(Resource):
    @jwt_required_endpoint
    def delete(self):
        # Gather parameters
        materia = request.args.get('materia')

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

        return create_response(message={'outcome': 'subject successfully deleted'}, status_code=STATUS_CODES["ok"])

class SubjectUpdate(Resource):
    @jwt_required_endpoint
    def patch(self):
        # Gather parameters
        materia = request.args.get('materia')
        toModify = request.args.get('toModify')
        newValue = request.args.get('newValue')

        # Check if the field to modify is allowed
        if toModify in ['materia']:
            return create_response(message={'outcome': 'error, specified field cannot be modified'}, status_code=STATUS_CODES["bad_request"])

        # Check if subject exists
        subject = fetchone_query('SELECT * FROM materie WHERE materia = %s', (materia,))
        if subject is None:
            return create_response(message={'outcome': 'error, specified subject does not exist'}, status_code=STATUS_CODES["not_found"])

        # Update the subject
        execute_query(f'UPDATE materie SET {toModify} = %s WHERE materia = %s', (newValue, materia))

        # Log the update
        log(type='info', 
            message=f'User {request.user_identity} updated subject {materia}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        return create_response(message={'outcome': 'subject successfully updated'}, status_code=STATUS_CODES["ok"])
    
class SubjectUnbind(Resource):
    @jwt_required_endpoint
    def delete(self):
        # Gather parameters
        idTurno = int(request.args.get('idTurno'))
        materia = request.args.get('materia')

        # Check if turn exists
        turn = fetchone_query('SELECT * FROM turni WHERE idTurno = %s', (idTurno,))
        if turn is None:
            return create_response(message={'outcome': 'error, specified turn does not exist'}, status_code=STATUS_CODES["not_found"])
        
        # Check if subject exists
        subject = fetchone_query('SELECT * FROM materie WHERE materia = %s', (materia,))
        if subject is None:
            return create_response(message={'outcome': 'error, specified subject does not exist'}, status_code=STATUS_CODES["not_found"])
        
        # Unbind the turn from the subject
        execute_query('DELETE FROM turnoMateria WHERE idTurno = %s AND materia = %s', (idTurno, materia))
        
        # Log the unbinding
        log(type='info', 
            message=f'User {request.user_identity} unbinded turn {idTurno} from subject {materia}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        return create_response(message={'outcome': 'success, turn unbinded from subject successfully'}, status_code=STATUS_CODES["ok"])
    
class SubjectRead(Resource):
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
        outcome = validate_filters(data=data, table_name='materie')
        if outcome != True:  # if the validation fails, outcome will be a dict with the error message
            return create_response(message=outcome, status_code=STATUS_CODES["bad_request"])

        try:
            # Build the query
            query, params = build_query_from_filters(data=data, table_name='materie', limit=limit, offset=offset)

            # Execute query
            subjects = fetchall_query(query, tuple(params))

            # Log the read
            log(type='info', 
                message=f'User {request.user_identity} read subjects with filters {data}', 
                origin_name=API_SERVER_NAME_IN_LOG, 
                origin_host=API_SERVER_HOST, 
                origin_port=API_SERVER_PORT)

            return create_response(message=subjects, status_code=STATUS_CODES["ok"])
        except Exception as err:
            return create_response(message={'error': str(err)}, status_code=STATUS_CODES["internal_error"])

# Add resources to the API
api.add_resource(SubjectRegister, '/register')
api.add_resource(SubjectDelete, '/delete')
api.add_resource(SubjectUpdate, '/update')
api.add_resource(SubjectUnbind, '/unbind')
api.add_resource(SubjectRead, '/read')
