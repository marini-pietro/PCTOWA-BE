from os.path import basename as os_path_basename
from flask import Blueprint, request, Response
from flask_restful import Api, Resource
from flask_jwt_extended import get_jwt_identity
from typing import List
from config import (API_SERVER_HOST, API_SERVER_PORT, 
                    API_SERVER_NAME_IN_LOG, STATUS_CODES)
from .blueprints_utils import (check_authorization, build_select_query_from_filters,
                               fetchone_query, fetchall_query, 
                               execute_query, log, 
                               jwt_required_endpoint, create_response, 
                               build_update_query_from_filters)

# Define constants
BP_NAME = os_path_basename(__file__).replace('_bp.py', '')

# Create the blueprint and API
address_bp = Blueprint(BP_NAME, __name__)
api = Api(address_bp)

class Address(Resource):
    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor'])
    def post(self) -> Response:
        """
        Creates a new address in the database.
        This endpoint requires authentication and authorization.
        The request must contain a JSON in the body and application/json as Content-Type.
        """

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
        
        # Validate parameters
        if idAzienda is not None:
            try:
                idAzienda = int(idAzienda)
            except ValueError:
                return create_response(message={'error': 'invalid idAzienda parameter'}, status_code=STATUS_CODES["bad_request"])

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
    def delete(self, id) -> Response:
        """
        Deletes an address from the database.
        This endpoint requires authentication and authorization.
        The request must contain the id parameter in the URI as a path variable.
        """
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
    def patch(self, id) -> Response:
        """
        Updates an address in the database.
        This endpoint requires authentication and authorization.
        The request must contain the id parameter in the URI as a path variable.
        """

        # Check that the request has a JSON body
        if not request.is_json or request.json is None:
            return create_response(message={'error': 'Request body must be valid JSON with Content-Type: application/json'}, status_code=STATUS_CODES["bad_request"])

        # Check if address exists
        address = fetchone_query('SELECT * FROM indirizzi WHERE idIndirizzo = %s', (id,))
        if address is None:
            return create_response(message={'outcome': 'error, specified address does not exist'}, status_code=STATUS_CODES["not_found"])
        
        # Check that the specified fields actually exist in the database
        modifiable_columns: set = {'stato', 'provincia', 'comune', 'cap', 'indirizzo', 'idAzienda'}
        toModify: list[str]  = list(request.json.keys())
        error_columns = [field for field in toModify if field not in modifiable_columns]
        if error_columns:
            return create_response(message={'outcome': f'error, field(s) {error_columns} do not exist or cannot be modified'}, status_code=STATUS_CODES["bad_request"])

        # Build the update query
        query, params = build_update_query_from_filters(data=request.json, table_name='indirizzi', 
                                                        id_column='idIndirizzo', id_value=id)

        # Update the address
        execute_query(query=query, params=params)

        # Log the update
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} updated address {id}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        # Return a success message
        return create_response(message={'outcome': f'address {id} successfully updated'}, status_code=STATUS_CODES["ok"])
    
    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor', 'teacher'])
    def get(self, id) -> Response:
        """
        Retrieves an address from the database.
        This endpoint requires authentication and authorization.
        The request must contain the id parameter in the URI as a path variable.
        """
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