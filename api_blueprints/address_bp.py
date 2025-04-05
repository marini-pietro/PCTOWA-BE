from flask import Blueprint, request
from flask_restful import Api, Resource
from flask_jwt_extended import get_jwt_identity
from config import API_SERVER_HOST, API_SERVER_PORT, API_SERVER_NAME_IN_LOG, STATUS_CODES
from .blueprints_utils import (check_authorization, build_select_query_from_filters,
                               fetchone_query, fetchall_query, 
                               execute_query, log, 
                               jwt_required_endpoint, create_response, 
                               validate_filters, build_update_query_from_filters)

# Create the blueprint and API
address_bp = Blueprint('address', __name__)
api = Api(address_bp)

class AddressRegister(Resource):
    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor'])
    def post(self):
        # Gather parameters
        stato = request.args.get('stato')
        provincia = request.args.get('provincia')
        comune = request.args.get('comune')
        cap = request.args.get('cap')
        indirizzo = request.args.get('indirizzo')
        try:
            idAzienda = int(request.args.get('idAzienda'))
        except (ValueError, TypeError):
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

        return create_response(message={'outcome': 'address successfully created'}, status_code=STATUS_CODES["created"])

class AddressDelete(Resource):
    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor'])
    def delete(self):
        # Gather parameters
        try:
            idIndirizzo = int(request.args.get('idIndirizzo'))
        except (ValueError, TypeError):
            return create_response(message={'error': 'invalid idIndirizzo parameter'}, status_code=STATUS_CODES["bad_request"])

        # Delete the address
        execute_query('DELETE FROM indirizzi WHERE idIndirizzo = %s', (idIndirizzo,))

        # Log the deletion
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} deleted address {idIndirizzo}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        return create_response(message={'outcome': 'address successfully deleted'}, status_code=STATUS_CODES["no_content"])

class AddressUpdate(Resource):
    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor'])
    def patch(self):
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
        try:
            idIndirizzo = int(request.args.get('idIndirizzo'))
        except (ValueError, TypeError):
            return create_response(message={'error': 'invalid idIndirizzo parameter'}, status_code=STATUS_CODES["bad_request"])

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
        address = fetchone_query('SELECT * FROM indirizzi WHERE idIndirizzo = %s', (idIndirizzo,))
        if address is None:
            return create_response(message={'outcome': 'error, specified address does not exist'}, status_code=STATUS_CODES["not_found"])

        # Build the update query
        query, params = build_update_query_from_filters(data=updates, table_name='indirizzi', id=idIndirizzo)

        # Update the address
        execute_query(query=query, params=params)

        # Log the update
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} updated address {idIndirizzo} with fields {toModify} and values {newValues}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        # Return a success message
        return create_response(message={'outcome': f'address {idIndirizzo} successfully updated'}, status_code=STATUS_CODES["ok"])

class AddressRead(Resource):
    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor', 'teacher'])
    def get(self):
        # Gather parameters with validation
        try:
            limit = int(request.args.get('limit', 10))  # Default limit to 10 if not provided
            offset = int(request.args.get('offset', 0))  # Default offset to 0 if not provided
        except ValueError:
            return create_response(message={'error': 'limit and offset must be integers'}, status_code=STATUS_CODES["bad_request"])

        idAzienda = request.args.get('idAzienda')
        try:
            idAzienda = int(idAzienda) if idAzienda else None
        except ValueError:
            return create_response(message={'error': 'idAzienda must be an integer'}, status_code=STATUS_CODES["bad_request"])

        # Build filter data dictionary
        data = {key: request.args.get(key) for key in ['idIndirizzo', 'stato', 'provincia', 'comune', 'cap', 'indirizzo']}
        if idAzienda is not None:
            data['idAzienda'] = idAzienda
        
        try:
            # Build the query
            query, params = build_select_query_from_filters(data=data, table_name='indirizzi', limit=limit, offset=offset)

            # Execute query
            addresses = fetchall_query(query, tuple(params))

            # Get the ids to log
            ids = [address['idIndirizzo'] for address in addresses]

            # Log the read
            log(type='info', 
                message=f'User {get_jwt_identity().get("email")} read addresses {ids}', 
                origin_name=API_SERVER_NAME_IN_LOG, 
                origin_host=API_SERVER_HOST, 
                origin_port=API_SERVER_PORT)

            # Return the results
            return create_response(message=addresses, status_code=STATUS_CODES["ok"])
        except Exception as err:
            return create_response(message={'error': str(err)}, status_code=STATUS_CODES["internal_error"])

# Add resources to the API
api.add_resource(AddressRegister, '/register')
api.add_resource(AddressDelete, '/delete')
api.add_resource(AddressUpdate, '/update')
api.add_resource(AddressRead, '/read')