from flask import Blueprint, jsonify, request
from flask_restful import Api, Resource
from config import API_SERVER_HOST, API_SERVER_PORT, API_SERVER_NAME_IN_LOG
import mysql.connector
from .blueprints_utils import validate_filters, fetchone_query, fetchall_query, execute_query, log, jwt_required_endpoint, parse_date_string, parse_time_string

# Create the blueprint and API
turn_bp = Blueprint('turn', __name__)
api = Api(turn_bp)

class TurnRegister(Resource):
    @jwt_required_endpoint
    def post(self):
        # Gather parameters
        settore = request.args.get('settore')
        posti = request.args.get('posti')
        ore = request.args.get('ore')
        idAzienda = int(request.args.get('idAzienda'))
        idIndirizzo = request.args.get('idIndirizzo')
        idTutor = request.args.get('idTutor')
        dataInizio = parse_date_string(date_string=request.args.get('dataInizio'))
        dataFine = parse_date_string(date_string=request.args.get('dataFine'))
        oraInizio = parse_time_string(time_string=request.args.get('oraInizio'))
        oraFine = parse_time_string(time_string=request.args.get('oraFine'))

        # Check if idAzienda exists
        company = fetchone_query('SELECT * FROM aziende WHERE idAzienda = %s', (idAzienda,))
        if company is None:
            return jsonify({'outcome': 'error, specified company does not exist'})

        # Check that idIndirizzo exists if provided
        if idIndirizzo is not None:
            address = fetchone_query('SELECT * FROM indirizzi WHERE idIndirizzo = %s', (int(idIndirizzo),))
            if address is None:
                return jsonify({'outcome': 'error, specified address does not exist'})

        # Check that settore exists if provided
        if settore is not None:
            sector = fetchone_query('SELECT * FROM settori WHERE settore = %s', (settore,))
            if sector is None:
                return jsonify({'outcome': 'error, specified sector does not exist'})

        # Check that idTutor exists if provided
        if idTutor is not None:
            tutor = fetchone_query('SELECT * FROM tutor WHERE idTutor = %s', (int(idTutor),))
            if tutor is None:
                return jsonify({'outcome': 'error, specified tutor does not exist'})

        # Insert the turn
        execute_query(
            'INSERT INTO turni (dataInizio, dataFine, settore, posti, ore, idAzienda, idIndirizzo, idTutor, oraInizio, oraFine) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
            (dataInizio, dataFine, settore, posti, ore, idAzienda, idIndirizzo, idTutor, oraInizio, oraFine)
        )

        # Log the turn creation
        log(type='info', 
            message=f'User {request.user_identity} created a turn', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        return jsonify({'outcome': 'turn successfully created'}), 201

class TurnDelete(Resource):
    @jwt_required_endpoint
    def delete(self):
        # Gather parameters
        idTurno = int(request.args.get('idTurno'))

        # Check if turn exists
        turn = fetchone_query('SELECT * FROM turni WHERE idTurno = %s', (idTurno,))
        if turn is None:
            return jsonify({'outcome': 'error, specified turn does not exist'})

        # Delete the turn
        execute_query('DELETE FROM turni WHERE idTurno = %s', (idTurno,))

        # Log the deletion
        log(type='info', 
            message=f'User {request.user_identity} deleted turn', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        return jsonify({'outcome': 'turn successfully deleted'})

class TurnUpdate(Resource):
    @jwt_required_endpoint
    def patch(self):
        # Gather parameters
        idTurno = int(request.args.get('idTurno'))
        toModify = request.args.get('toModify')
        newValue = request.args.get('newValue')

        # Check if the field to modify is allowed
        if toModify in ['idTurno']:
            return jsonify({'outcome': 'error, specified field cannot be modified'})

        # Check if any casting operations are needed
        if toModify in ['posti', 'ore']:
            newValue = int(newValue)
        elif toModify in ['dataInizio', 'dataFine']:
            newValue = parse_date_string(date_string=newValue)
        elif toModify in ['oraInizio', 'oraFine']:
            newValue = parse_time_string(time_string=newValue)

        # Check if turn exists
        turn = fetchone_query('SELECT * FROM turni WHERE idTurno = %s', (idTurno,))
        if turn is None:
            return jsonify({'outcome': 'error, specified turn does not exist'})

        # Update the turn
        execute_query(f'UPDATE turni SET {toModify} = %s WHERE idTurno = %s', (newValue, idTurno))

        # Log the update
        log(type='info', 
            message=f'User {request.user_identity} updated turn', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        return jsonify({'outcome': 'turn successfully updated'})

class TurnRead(Resource):
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
        outcome = validate_filters(data=data, table_name='turni')
        if outcome != True:  # if the validation fails, outcome will be a dict with the error message
            return jsonify(outcome), 400

        try:
            # Build the query
            filters_keys = list(data.keys()) if isinstance(data, dict) else []
            filters = " AND ".join([f"{key} = %s" for key in filters_keys])
            query = f"SELECT * FROM turni WHERE {filters} LIMIT %s OFFSET %s" if filters else "SELECT * FROM indirizzi LIMIT %s OFFSET %s"
            params = [data[key] for key in filters_keys] + [limit, offset]

            # Execute query
            turns = fetchall_query(query, tuple(params))

            # Log the read
            log(type='info', 
                message=f'User {request.user_identity} read turns with filters: {data}', 
                origin_name=API_SERVER_NAME_IN_LOG, 
                origin_host=API_SERVER_HOST, 
                origin_port=API_SERVER_PORT)

            return jsonify(turns), 200
        except Exception as err:
            return jsonify({'error': str(err)}), 500

class TurnBind(Resource):
    @jwt_required_endpoint
    def post(self):
        # Gather parameters
        idTurno = int(request.args.get('idTurno'))
        settore = request.args.get('settore')

        # Check if turn exists
        turn = fetchone_query('SELECT * FROM turni WHERE idTurno = %s', (idTurno,))
        if turn is None:
            return jsonify({'outcome': 'error, specified turn does not exist'})

        # Check if sector exists
        sector = fetchone_query('SELECT * FROM settori WHERE settore = %s', (settore,))
        if sector is None:
            return jsonify({'outcome': 'error, specified sector does not exist'})

        # Bind the sector to the turn
        execute_query('INSERT INTO turniSettore (idTurno, settore) VALUES (%s, %s)', (idTurno, settore))

        # Log the binding
        log(type='info', 
            message=f'User {request.user_identity} binded sector to turn', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        return jsonify({'outcome': 'sector binded to turn successfully'})

# Add resources to the API
api.add_resource(TurnRegister, '/register')
api.add_resource(TurnDelete, '/delete')
api.add_resource(TurnUpdate, '/update')
api.add_resource(TurnRead, '/read')
api.add_resource(TurnBind, '/bind_sector')