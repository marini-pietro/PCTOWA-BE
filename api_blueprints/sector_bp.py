from flask import Blueprint, jsonify, request
from flask_restful import Api, Resource
from utils import fetchone_query, execute_query, log, jwt_required_endpoint

# Create the blueprint and API
subjects_bp = Blueprint('sector', __name__)
api = Api(subjects_bp)

class SectorRegister(Resource):
    @jwt_required_endpoint()
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
        log('info', f'User {request.user_identity} created sector {settore}')

        return jsonify({'outcome': 'sector successfully created'}), 201

class SectorDelete(Resource):
    @jwt_required_endpoint()
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
        log('info', f'User {request.user_identity} deleted sector {settore}')

        return jsonify({'outcome': 'sector successfully deleted'})

class SectorUpdate(Resource):
    @jwt_required_endpoint()
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
        log('info', f'User {request.user_identity} updated sector {settore}')

        return jsonify({'outcome': 'sector successfully updated'})
    
class SectorBind(Resource):
    @jwt_required_endpoint()
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
        log('info', f'User {request.user_identity} binded turn {idTurno} to sector {settore}')

        return jsonify({'outcome': 'success, turn binded to sector successfully'})

# Add resources to the API
api.add_resource(SectorRegister, '/register')
api.add_resource(SectorDelete, '/delete')
api.add_resource(SectorUpdate, '/update')
