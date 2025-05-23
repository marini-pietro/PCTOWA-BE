from os.path import basename as os_path_basename
from flask import Blueprint, request, Response
from flask_restful import Api, Resource
from flask_jwt_extended import get_jwt_identity
from typing import List
from config import (API_SERVER_HOST, API_SERVER_PORT, 
                    API_SERVER_NAME_IN_LOG, STATUS_CODES)
from .blueprints_utils import (check_authorization, fetchone_query, 
                               fetchall_query, execute_query, 
                               log, jwt_required_endpoint, 
                               create_response, parse_date_string, 
                               parse_time_string, build_select_query_from_filters, 
                               build_update_query_from_filters)

# Define constants
BP_NAME = os_path_basename(__file__).replace('_bp.py', '')

# Create the blueprint and API
turn_bp = Blueprint(BP_NAME, __name__)
api = Api(turn_bp)

class Turn(Resource):
    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor'])
    def post(self) -> Response:
        """
        Create a new turn.
        The request body must be a JSON object with application/json content type.
        """
        
        # Ensure the request has a JSON body
        if not request.is_json or request.json is None:
            return create_response(message={'error': 'Request body must be valid JSON with Content-Type: application/json'}, status_code=STATUS_CODES["bad_request"])
        
        # Gather parameters
        settore = request.json.get('settore')
        materia = request.json.get('materia')
        dataInizio = parse_date_string(date_string=request.json.get('dataInizio'))
        dataFine = parse_date_string(date_string=request.json.get('dataFine'))
        oraInizio = parse_time_string(time_string=request.json.get('oraInizio'))
        oraFine = parse_time_string(time_string=request.json.get('oraFine'))
        giornoInizio = request.json.get('giornoInizio')
        giornoFine = request.json.get('giornoFine')
        ore = request.json.get('ore')
        posti = request.json.get('posti')
        idIndirizzo = request.json.get('idIndirizzo')
        idTutor = request.json.get('idTutor')
        idAzienda = request.json.get('idAzienda')
        
        # Validate data
        valid_days = ['lunedì', 'martedì', 'mercoledì', 'giovedì', 'venerdì']
        if giornoInizio not in valid_days:
            return create_response(message={'error': 'invalid giornoInizio value'}, status_code=STATUS_CODES["bad_request"])
        if giornoFine not in valid_days:
            return create_response(message={'error': 'invalid giornoFine value'}, status_code=STATUS_CODES["bad_request"])
        if valid_days.index(giornoInizio) >= valid_days.index(giornoFine):
            return create_response(message={'error': 'giornoInizio must be before giornoFine'}, status_code=STATUS_CODES["bad_request"])
        if giornoInizio == giornoFine:
            return create_response(message={'error': 'giornoInizio and giornoFine cannot be the same'}, status_code=STATUS_CODES["bad_request"])
        
        values_to_check = {"ore": ore, "posti": posti, "idIndirizzo": idIndirizzo, "idTutor": idTutor, "idAzienda": idAzienda}
        for key, value in values_to_check.items():
            if value is not None:
                try:
                    values_to_check[key] = int(value)
                except (ValueError, TypeError):
                    return create_response(message={'error': f'invalid {key} value'}, status_code=STATUS_CODES["bad_request"])

        # CHECK THAT VALUES PROVIDED ACTUALLY EXIST IN THE DATABASE
        pk_to_check = {
            "aziende": ["idAzienda", idAzienda], 
            "indirizzi": ["idIndirizzo", idIndirizzo], 
            "tutor": ["idTutor", idTutor],
            "materie": ["materia", materia],
            "settori": ["settore", settore]
        }
        for table, (column, value) in pk_to_check.items():
            if value is not None:
                # Check if the value exists in the database
                result = fetchone_query(f'SELECT * FROM {table} WHERE {column} = %s', (value,))
                if result is None:
                    return create_response(message={'outcome': f'error, specified row in table {table} does not exist'}, status_code=STATUS_CODES["not_found"])

        # INSERT THE DATA INTO THE DATABASE
        # Insert the turn
        lastrowid = execute_query(
            'INSERT INTO turni (dataInizio, dataFine, settore, posti, ore, idAzienda, idIndirizzo, idTutor, oraInizio, oraFine) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
            (dataInizio, dataFine, settore, posti, ore, idAzienda, idIndirizzo, idTutor, oraInizio, oraFine)
        )

        # Insert row into turnoSettore table
        if settore is not None:
            execute_query(
                'INSERT INTO turnoSettore (idTurno, settore) VALUES (%s, %s)',
                (lastrowid, settore)
            )

        # Insert row into turnoMateria table
        if materia is not None:
            execute_query(
                'INSERT INTO turnoMateria (idTurno, materia) VALUES (%s, %s)',
                (lastrowid, materia)
            )

        # Log the turn creation
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} created turn {lastrowid}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        # Return a success message
        return create_response(message={'outcome': 'turn successfully created',
                                        'location': f'http://{API_SERVER_HOST}:{API_SERVER_PORT}/api/{BP_NAME}/{lastrowid}'}, status_code=STATUS_CODES["created"])

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor'])
    def delete(self, id) -> Response:
        """
        Delete a turn.
        The request must include the turn ID as a path variable.
        """
        # Delete the turn
        execute_query('DELETE FROM turni WHERE idTurno = %s', (id,))

        # Log the deletion
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} deleted turn {id}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        # Return a success message
        return create_response(message={'outcome': 'turn successfully deleted'}, status_code=STATUS_CODES["no_content"])

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor'])
    def patch(self, id) -> Response:
        """
        Update a turn.
        The request must include the turn ID as a path variable.
        """

        # Ensure the request has a JSON body
        if not request.is_json or request.json is None:
            return create_response(message={'error': 'Request body must be valid JSON with Content-Type: application/json'}, status_code=STATUS_CODES["bad_request"])
            
        # Check that the specified class exists
        turn = fetchone_query('SELECT * FROM turni WHERE idTurno = %s', (id,))
        if not turn:
            return create_response(message={'outcome': 'specified turn does not exist'}, status_code=STATUS_CODES["not_found"])

        # Check that the specified fields actually exist in the database
        modifiable_columns: List[str] = ['dataInizio', 'dataFine', 
                              'posti', 'postiOccupati', 
                              'ore', 'idAzienda', 
                              'idTutor', 'idIndirizzo', 
                              'oraInizio', 'oraFine',
                              'giornoInizio', 'giornoFine']
        toModify: list[str]  = list(request.json.keys())
        error_columns = [field for field in toModify if field not in modifiable_columns]
        if error_columns:
            return create_response(message={'outcome': f'error, field(s) {error_columns} do not exist or cannot be modified'}, status_code=STATUS_CODES["bad_request"])

        # Build the update query
        query, params = build_update_query_from_filters(data=request.json, table_name='turni', 
                                                        id_column='idTurno', id_value=id)

        # Execute the update query
        execute_query(query, params)

        # Log the update
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} updated turn {id}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        # Return a success message
        return create_response(message={'outcome': 'turn successfully updated'}, status_code=STATUS_CODES["ok"])

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor', 'teacher'])
    def get(self, id) -> Response:
        """
        Get a turn by ID.
        The request must include the turn ID as a path variable.
        """
        # Gather parameters
        dataInizio = parse_date_string(date_string=request.args.get('dataInizio'))
        dataFine = parse_date_string(date_string=request.args.get('dataFine'))
        oraInizio = parse_time_string(time_string=request.args.get('oraInizio'))
        oraFine = parse_time_string(time_string=request.args.get('oraFine'))
        try:
            posti = int(request.args.get('posti')) if request.args.get('posti') else None
        except (ValueError, TypeError):
            return create_response(message={'error': 'invalid posti value'}, status_code=STATUS_CODES["bad_request"])
        try:
            postiOccupati = int(request.args.get('postiOccupati')) if request.args.get('postiOccupati') else None
        except (ValueError, TypeError):
            return create_response(message={'error': 'invalid postiOccupati value'}, status_code=STATUS_CODES["bad_request"])
        try:
            ore = request.args.get('ore')
        except (ValueError, TypeError):
            return create_response(message={'error': 'invalid ore value'}, status_code=STATUS_CODES["bad_request"])
        try:
            idAzienda = int(request.args.get('idAzienda')) if request.args.get('idAzienda') else None
        except (ValueError, TypeError):
            return create_response(message={'error': 'invalid idAzienda value'}, status_code=STATUS_CODES["bad_request"])
        try:
            idTutor = int(request.args.get('idTutor')) if request.args.get('idTutor') else None
        except (ValueError, TypeError):
            return create_response(message={'error': 'invalid idTutor value'}, status_code=STATUS_CODES["bad_request"])
        try:
            idIndirizzo = request.args.get('idIndirizzo')
        except (ValueError, TypeError):
            return create_response(message={'error': 'invalid idIndirizzo value'}, status_code=STATUS_CODES["bad_request"])
        try:
            limit = int(request.args.get('limit', 10))  # Default limit to 10 if not provided
            offset = int(request.args.get('offset', 0))  # Default offset to 0 if not provided
        except (ValueError, TypeError):
            return create_response(message={'error': 'invalid limit or offset parameter'}, status_code=STATUS_CODES["bad_request"])

        # Build the filters dictionary (only include non-null values)
        data = {key: value for key, value in {
            'idTurno': id,  # Use the path variable 'id'
            'dataInizio': dataInizio,
            'dataFine': dataFine,
            'oraInizio': oraInizio,
            'oraFine': oraFine,
            'posti': posti,
            'postiOccupati': postiOccupati,
            'ore': ore,
            'idAzienda': idAzienda,
            'idTutor': idTutor,
            'idIndirizzo': idIndirizzo
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

            # Get the ids to log
            ids = [turn['idTurno'] for turn in turns]

            # Log the read
            log(type='info', 
                message=f'User {get_jwt_identity().get("email")} read turns {ids}', 
                origin_name=API_SERVER_NAME_IN_LOG, 
                origin_host=API_SERVER_HOST, 
                origin_port=API_SERVER_PORT)

            # Return the results
            return create_response(message=turns, status_code=STATUS_CODES["ok"])
        except Exception as err:
            return create_response(message={'error': str(err)}, status_code=STATUS_CODES["internal_error"])

api.add_resource(Turn, f'/{BP_NAME}', f'/{BP_NAME}/<int:id>')