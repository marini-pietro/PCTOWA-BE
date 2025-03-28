from flask import Blueprint, jsonify, request
from flask_restful import Api, Resource
from config import API_SERVER_HOST, API_SERVER_PORT, API_SERVER_NAME_IN_LOG
from .blueprints_utils import validate_filters, build_query_from_filters, fetchone_query, fetchall_query, execute_query, log, jwt_required_endpoint

# Create the blueprint and API
sector_bp = Blueprint('sector', __name__)
api = Api(sector_bp)

class SectorRegister(Resource):
    @jwt_required_endpoint
    def post(self):
        # Gather parameters
        settore = request.args.get('settore')

        # Check if sector exists
        sector = fetchone_query('SELECT * FROM settori WHERE settore = %s', (settore,))
        if sector is not None:
            return jsonify({'outcome': 'error, specified sector already exists'})

        # Insert the sector
        execute_query('INSERT INTO settori (settore) VALUES (%s)', (settore,))

        # Log the sector creation
        log(type='info',
            message=f'User {request.user_identity} created sector {settore}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        return jsonify({'outcome': 'sector successfully created'}), 201

class SectorDelete(Resource):
    @jwt_required_endpoint
    def delete(self):
        # Gather parameters
        settore = request.args.get('settore')

        # Check if sector exists
        sector = fetchone_query('SELECT * FROM settori WHERE settore = %s', (settore,))
        if sector is None:
            return jsonify({'outcome': 'error, specified sector does not exist'})

        # Delete the sector
        execute_query('DELETE FROM settori WHERE settore = %s', (settore,))

        # Log the deletion
        log(type='info',
            message=f'User {request.user_identity} deleted sector {settore}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        return jsonify({'outcome': 'sector successfully deleted'})

class SectorUpdate(Resource):
    @jwt_required_endpoint
    def patch(self):
        # Gather parameters
        settore = request.args.get('settore')
        newValue = request.args.get('newValue')

        # Check if sector exists
        sector = fetchone_query('SELECT * FROM settori WHERE settore = %s', (settore,))
        if sector is None:
            return jsonify({'outcome': 'error, specified sector does not exist'})

        # Update the sector
        execute_query('UPDATE settori SET settore = %s WHERE settore = %s', (newValue, settore))

        # Log the update
        log(type='info', 
            message=f'User {request.user_identity} updated sector {settore}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        return jsonify({'outcome': 'sector successfully updated'})
    
class SectorBind(Resource):
    @jwt_required_endpoint
    def post(self):
        # Gather parameters
        idTurno = int(request.args.get('idTurno'))
        settore = request.args.get('settore')

        # Check if turn exists
        turn = fetchone_query('SELECT * FROM turni WHERE idTurno = %s', (idTurno,))
        if turn is None:
            return {'outcome': 'error, specified turn does not exist'}
        
        # Check if sector exists
        sector = fetchone_query('SELECT * FROM settori WHERE settore = %s', (settore,))
        if sector is None:
            return {'outcome': 'error, specified sector does not exist'}
        
        # Bind the turn to the sector
        execute_query('INSERT INTO turnoSectore (idTurno, settore) VALUES (%s, %s)', (idTurno, settore))
        
        # Log the binding
        log(type='info', 
            message=f'User {request.user_identity} binded turn {idTurno} to sector {settore}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        return jsonify({'outcome': 'success, turn binded to sector successfully'})

class SectorRead(Resource):
    @jwt_required_endpoint
    def get(self):
        # Gather URL parameters
        try:
            limit = int(request.args.get('limit'))
            offset = int(request.args.get('offset'))
        except (ValueError, TypeError):
            return jsonify({'error': 'invalid limit or offset parameter'}), 400

        # Gather json filters
        data = request.get_json()

        # Validate filters
        outcome = validate_filters(data=data, table_name='settori')
        if outcome != True:  # if the validation fails, outcome will be a dict with the error message
            return jsonify(outcome), 400

        try:
            # Build the query
            query, params = build_query_from_filters(data=data, table_name='settori', limit=limit, offset=offset)

            # Execute query
            sectors = fetchone_query(query, tuple(params))

            # Log the read
            log(type='info', 
                message=f'User {request.user_identity} read sectors with filters {data}', 
                origin_name=API_SERVER_NAME_IN_LOG, 
                origin_host=API_SERVER_HOST, 
                origin_port=API_SERVER_PORT)

            return jsonify(sectors), 200
        except Exception as err:
            return jsonify({'error': str(err)}), 500

# Add resources to the API
api.add_resource(SectorRegister, '/register')
api.add_resource(SectorDelete, '/delete')
api.add_resource(SectorUpdate, '/update')
api.add_resource(SectorBind, '/bind')
api.add_resource(SectorRead, '/read')
