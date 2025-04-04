from flask import Blueprint, request
from flask_restful import Api, Resource
from config import API_SERVER_HOST, API_SERVER_PORT, API_SERVER_NAME_IN_LOG, STATUS_CODES
from .blueprints_utils import (check_authorization, validate_filters, 
                               fetchone_query, fetchall_query, 
                               execute_query, log, 
                               jwt_required_endpoint, create_response, 
                               parse_date_string, parse_time_string, 
                               build_select_query_from_filters, build_update_query_from_filters)

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
        idIndirizzo = request.args.get('idIndirizzo')
        idTutor = request.args.get('idTutor')
        dataInizio = parse_date_string(date_string=request.args.get('dataInizio'))
        dataFine = parse_date_string(date_string=request.args.get('dataFine'))
        oraInizio = parse_time_string(time_string=request.args.get('oraInizio'))
        oraFine = parse_time_string(time_string=request.args.get('oraFine'))
        try:
            idAzienda = int(request.args.get('idAzienda'))
        except (ValueError, TypeError):
            return create_response(message={'outcome': 'invalid idAzienda value'}, status_code=STATUS_CODES["bad_request"])

        # Check that specified company exists
        company = fetchone_query('SELECT * FROM aziende WHERE idAzienda = %s', (idAzienda,))
        if company is None:
            return create_response(message={'outcome': 'error, specified company does not exist'}, status_code=STATUS_CODES["not_found"])

        # Check that idIndirizzo exists if provided
        if idIndirizzo is not None:
            address = fetchone_query('SELECT * FROM indirizzi WHERE idIndirizzo = %s', (int(idIndirizzo),))
            if address is None:
                return create_response(message={'outcome': 'error, specified address does not exist'}, status_code=STATUS_CODES["not_found"])

        # Check that settore exists if provided
        if settore is not None:
            sector = fetchone_query('SELECT * FROM settori WHERE settore = %s', (settore,))
            if sector is None:
                return create_response(message={'outcome': 'error, specified sector does not exist'}, status_code=STATUS_CODES["not_found"])

        # Check that idTutor exists if provided
        if idTutor is not None:
            tutor = fetchone_query('SELECT * FROM tutor WHERE idTutor = %s', (int(idTutor),))
            if tutor is None:
                return create_response(message={'outcome': 'error, specified tutor does not exist'}, status_code=STATUS_CODES["not_found"])

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

        # Return a success message
        return create_response(message={'outcome': 'turn successfully created'}, status_code=STATUS_CODES["created"])

class TurnDelete(Resource):
    @jwt_required_endpoint
    def delete(self):
        # Gather parameters
        try:
            idTurno = int(request.args.get('idTurno'))
        except (ValueError, TypeError):
            return create_response(message={'error': 'invalid idTurno value'}, status_code=STATUS_CODES["bad_request"])

        # Delete the turn
        execute_query('DELETE FROM turni WHERE idTurno = %s', (idTurno,))

        # Log the deletion
        log(type='info', 
            message=f'User {request.user_identity} deleted turn {idTurno}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        # Return a success message
        return create_response(message={'outcome': 'turn successfully deleted'}, status_code=STATUS_CODES["no_content"])

class TurnUpdate(Resource):
    @jwt_required_endpoint
    def patch(self):
        # Gather parameters
        toModify = request.args.get('toModify').split(',')
        newValues = request.args.get('newValue').split(',')
        try:
            idTurno = int(request.args.get('idTurno'))
        except (ValueError, TypeError):
            return create_response(message={'error': 'invalid idTurno value'}, status_code=STATUS_CODES["bad_request"])
        
        # Validate parameters
        if len(toModify) != len(newValues):
            return create_response(message={'outcome': 'Mismatched fields and values lists lengths'}, status_code=STATUS_CODES["bad_request"])

        # Build a dictionary with fields as keys and values as values
        updates = dict(zip(toModify, newValues))  # {field1: value1, field2: value2, ...}

        # Check that the specified fields can be modified
        not_allowed_fields = ['idTurno']
        for field in toModify:
            if field in not_allowed_fields:
                return create_response(message={'outcome': f'error, field {field} cannot be modified'}, status_code=STATUS_CODES["bad_request"])
            
        # Check that the specified fields actually exist in the database
        outcome = validate_filters(data=updates, table_name='turni')
        if outcome != True:  # if the validation fails, outcome will be a dict with the error message
            return create_response(outcome, STATUS_CODES["bad_request"])
        
        # Check that the specified class exists
        turn = fetchone_query('SELECT * FROM turni WHERE idTurno = %s', (idTurno,))
        if not turn:
            return create_response(message={'outcome': 'specified turn does not exist'}, status_code=STATUS_CODES["not_found"])

        # Build the update query
        query, params = build_update_query_from_filters(data=updates, table_name='turni', id=idTurno)

        # Execute the update query
        execute_query(query, params)

        # Log the update
        log(type='info', 
            message=f'User {request.user_identity} updated turn {idTurno}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        # Return a success message
        return create_response(message={'outcome': 'turn successfully updated'}, status_code=STATUS_CODES["ok"])

class TurnRead(Resource):
    @jwt_required_endpoint
    def get(self):
        # Gather parameters
        dataInizio = parse_date_string(date_string=request.args.get('dataInizio'))
        dataFine = parse_date_string(date_string=request.args.get('dataFine'))
        oraInizio = parse_time_string(time_string=request.args.get('oraInizio'))
        oraFine = parse_time_string(time_string=request.args.get('oraFine'))
        try:
            posti = int(request.args.get('posti'))
        except (ValueError, TypeError):
            return create_response(message={'error': 'invalid posti value'}, status_code=STATUS_CODES["bad_request"])
        try:
            postiOccupati = int(request.args.get('postiOccupati'))
        except (ValueError, TypeError):
            return create_response(message={'error': 'invalid postiOccupati value'}, status_code=STATUS_CODES["bad_request"])
        try:
            ore = request.args.get('ore')
        except (ValueError, TypeError):
            return create_response(message={'error': 'invalid ore value'}, status_code=STATUS_CODES["bad_request"])
        try:
            idAzienda = int(request.args.get('idAzienda'))
        except (ValueError, TypeError):
            return create_response(message={'error': 'invalid idAzienda value'}, status_code=STATUS_CODES["bad_request"])
        try:
            idTutor = int(request.args.get('idTutor'))
        except (ValueError, TypeError):
            return create_response(message={'error': 'invalid idTutor value'}, status_code=STATUS_CODES["bad_request"])
        try:
            idIndirizzo = request.args.get('idIndirizzo')
        except (ValueError, TypeError):
            return create_response(message={'error': 'invalid idIndirizzo value'}, status_code=STATUS_CODES["bad_request"])
        try:
            idTurno = int(request.args.get('idTurno'))
        except (ValueError, TypeError):
            return create_response(message={'error': 'invalid idTurno value'}, status_code=STATUS_CODES["bad_request"])
        try:
            limit = int(request.args.get('limit'))
            offset = int(request.args.get('offset'))
        except (ValueError, TypeError):
            return create_response(message={'error': 'invalid limit or offset parameter'}, status_code=STATUS_CODES["bad_request"])

        # Build the filters dictionary (only include non-null values)
        data = {key: value for key, value in {
            'dataInizio': dataInizio,
            'dataFine': dataFine,
            'oraInizio': oraInizio,
            'oraFine': oraFine,
            'posti': posti,
            'postiOccupati': postiOccupati,
            'ore': ore,
            'idAzienda': idAzienda,
            'idTutor': idTutor,
            'idIndirizzo': idIndirizzo,
            'idTurno': idTurno
        }.items() if value}

        try:
            # Build the query
            query, params = build_select_query_from_filters(
                data=data, 
                table_name='turni',
                limit=limit, 
                offset=offset
            )

            # Execute query
            turns = fetchall_query(query, tuple(params))

            # Log the read
            log(type='info', 
                message=f'User {request.user_identity} read turns with filters: {data}', 
                origin_name=API_SERVER_NAME_IN_LOG, 
                origin_host=API_SERVER_HOST, 
                origin_port=API_SERVER_PORT)

            # Return the results
            return create_response(message=turns, status_code=STATUS_CODES["ok"])
        except Exception as err:
            return create_response(message={'error': str(err)}, status_code=STATUS_CODES["internal_error"])

# Add resources to the API
api.add_resource(TurnRegister, '/register')
api.add_resource(TurnDelete, '/delete')
api.add_resource(TurnUpdate, '/update')
api.add_resource(TurnRead, '/read')