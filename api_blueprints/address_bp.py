from os.path import basename as os_path_basename
from flask import Blueprint, request
from flask_restful import Api, Resource
from flask_jwt_extended import get_jwt_identity
from config import API_SERVER_HOST, API_SERVER_PORT, API_SERVER_NAME_IN_LOG, STATUS_CODES
from .blueprints_utils import (check_authorization, build_select_query_from_filters,
                               fetchone_query, fetchall_query, 
                               execute_query, log, 
                               jwt_required_endpoint, create_response, 
                               validate_filters, build_update_query_from_filters)

# Define constants
BP_NAME = os_path_basename(__file__).replace('_bp.py', '')

# Create the blueprint and API
address_bp = Blueprint(BP_NAME, __name__)
api = Api(address_bp)

class Address(Resource):
    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor'])
    def post(self):
        # Ensure the request has a JSON body
        if not request.is_json or request.json is None:
            return create_response(message={'error': 'Request body must be valid JSON with Content-Type: application/json'}, status_code=STATUS_CODES["bad_request"])

        # Gather parameters
        stato = request.json.get('stato')
        provincia = request.json.get('provincia')
        comune = request.json.get('comune')
        cap = request.json.get('cap')
        indirizzo = request.json.get('indirizzo')
        idAzienda = request.json.get('idAzienda')
        if isinstance(idAzienda, str) and idAzienda.isdigit():
            idAzienda = int(idAzienda)
        elif not isinstance(idAzienda, int):
            return create_response(message={'error': 'invalid idAzienda JSON value'}, status_code=STATUS_CODES["bad_request"])

        # Check if idAzienda exists
        company = fetchone_query('SELECT * FROM aziende WHERE idAzienda = %s', (idAzienda,))
        if company is None:
            return create_response(message={'outcome': 'error, specified company does not exist'}, status_code=STATUS_CODES["not_found"])

        # Insert the address
        lastrowid = execute_query(
            'INSERT INTO indirizzi (stato, provincia, comune, cap, indirizzo, idAzienda) VALUES (%s, %s, %s, %s, %s, %s)',
            (stato, provincia, comune, cap, indirizzo, idAzienda)
        )

        # Log the address creation
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} created address {lastrowid}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        return create_response(message={'outcome': 'address successfully created', 
                                        'location': f'http://{API_SERVER_HOST}:{API_SERVER_PORT}/api/{BP_NAME}/{lastrowid}'}, status_code=STATUS_CODES["created"])
    
    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor'])
    def delete(self, id):
        # Delete the address
        execute_query('DELETE FROM indirizzi WHERE idIndirizzo = %s', (id,))

        # Log the deletion
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} deleted address {id}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        return create_response(message={'outcome': 'address successfully deleted'}, status_code=STATUS_CODES["no_content"])
    
    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor'])
    def patch(self, id):
        """
        Updates an address in the database.
        This endpoint requires authentication and authorization, only users with the 'admin' role can access it.
        The request must contain the following parameters:
        - idIndirizzo: The ID of the address to update.
        - toModify: A comma-separated list of fields to modify (cannot contain primary key idIndirizzo).
        - newValue: A comma-separated list of new values for the fields to modify.
        """

        # Gather parameters
        toModify: list[str]  = request.args.get('toModify').split(',')
        newValues: list[str] = request.args.get('newValue').split(',')

        # Validate parameters
        if len(toModify) != len(newValues):
            return create_response(message={'outcome': 'Mismatched fields and values lists lengths'}, status_code=STATUS_CODES["bad_request"])

        # Build a dictionary with fields as keys and values as values
        updates = dict(zip(toModify, newValues))  # {field1: value1, field2: value2, ...}

        # Check that the fields to modify can be modified
        not_allowed_fields: list[str] = ['idIndirizzo']
        for field in toModify:
            if field in not_allowed_fields:
                return create_response(message={'outcome': f'error, field "{field}" cannot be modified'}, status_code=STATUS_CODES["forbidden"])

        # Check that the specified fields actually exist in the database
        outcome = validate_filters(toModify, 'indirizzi')
        if outcome is not True:
            return create_response(message=outcome, status_code=STATUS_CODES["bad_request"])

        # Check if address exists
        address = fetchone_query('SELECT * FROM indirizzi WHERE idIndirizzo = %s', (id,))
        if address is None:
            return create_response(message={'outcome': 'error, specified address does not exist'}, status_code=STATUS_CODES["not_found"])

        # Build the update query
        query, params = build_update_query_from_filters(data=updates, table_name='indirizzi', id=id)

        # Update the address
        execute_query(query=query, params=params)

        # Log the update
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} updated address {id} with fields {toModify} and values {newValues}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        # Return a success message
        return create_response(message={'outcome': f'address {id} successfully updated'}, status_code=STATUS_CODES["ok"])
    
    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor', 'teacher'])
    def get(self, id):
        # Gather parameters
        try:
            limit = int(request.args.get('limit', 10))  # Default limit to 10 if not provided
            offset = int(request.args.get('offset', 0))  # Default offset to 0 if not provided
        except ValueError:
            return create_response(message={'error': 'limit and offset must be integers'}, status_code=STATUS_CODES["bad_request"])
        try:
            idAzienda = int(request.args.get('idAzienda'))
        except ValueError:
            return create_response(message={'error': 'invalid idAzienda parameter'}, status_code=STATUS_CODES["bad_request"])

        # Build filter data dictionary
        data = {key: request.args.get(key) for key in ['idIndirizzo', 'stato', 'provincia', 'comune', 'cap', 'indirizzo']}
        if idAzienda is not None:
            data['idAzienda'] = idAzienda

        # If 'id' is provided, add it to the filter
        if id is not None:
            data['idIndirizzo'] = id

        try:
            # Build the query
            query, params = build_select_query_from_filters(data=data, table_name='indirizzi', limit=limit, offset=offset)

            # Execute query
            addresses = fetchall_query(query, params)

            # Get the ids to log
            ids = [address['idIndirizzo'] for address in addresses]

            # Log the read
            log(type='info', 
                message=f'User {get_jwt_identity().get("email")} read address {ids}', 
                origin_name=API_SERVER_NAME_IN_LOG, 
                origin_host=API_SERVER_HOST, 
                origin_port=API_SERVER_PORT)

            # Return the results
            return create_response(message=addresses, status_code=STATUS_CODES["ok"])
        except Exception as err:
            return create_response(message={'error': str(err)}, status_code=STATUS_CODES["internal_error"])
    
api.add_resource(Address, f'/{BP_NAME}', f'/{BP_NAME}/<int:id>')