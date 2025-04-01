from flask import Blueprint, request
from flask_restful import Api, Resource
from config import API_SERVER_HOST, API_SERVER_PORT, API_SERVER_NAME_IN_LOG, STATUS_CODES
from .blueprints_utils import validate_filters, validate_inputs, build_query_from_filters, fetchone_query, fetchall_query, execute_query, log, jwt_required_endpoint, create_response

# Create the blueprint and API
address_bp = Blueprint('address', __name__)
api = Api(address_bp)

class AddressRegister(Resource):
    @jwt_required_endpoint
    def post(self):
        # Gather parameters
        stato = request.args.get('stato')
        provincia = request.args.get('provincia')
        comune = request.args.get('comune')
        cap = request.args.get('cap')
        indirizzo = request.args.get('indirizzo')
        idAzienda = int(request.args.get('idAzienda'))

        # Check if idAzienda exists
        company = fetchone_query('SELECT * FROM aziende WHERE idAzienda = %s', (idAzienda,))
        if company is None:
            return create_response(message={'outcome': 'error, specified company does not exist'}, status_code=STATUS_CODES["not_found"])

        # Insert the address
        execute_query(
            'INSERT INTO indirizzi (stato, provincia, comune, cap, indirizzo, idAzienda) VALUES (%s, %s, %s, %s, %s, %s)',
            (stato, provincia, comune, cap, indirizzo, idAzienda)
        )

        # Log the address creation
        log(type='info', 
            message=f'User {request.user_identity} created address', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        return create_response(message={'outcome': 'address successfully created'}, status_code=STATUS_CODES["created"])

class AddressDelete(Resource):
    @jwt_required_endpoint
    def delete(self):
        # Gather parameters
        idIndirizzo = int(request.args.get('idIndirizzo'))

        # Check if address exists
        address = fetchone_query('SELECT * FROM indirizzi WHERE idIndirizzo = %s', (idIndirizzo,))
        if address is None:
            return create_response(message={'outcome': 'error, specified address does not exist'}, status_code=STATUS_CODES["not_found"])

        # Delete the address
        execute_query('DELETE FROM indirizzi WHERE idIndirizzo = %s', (idIndirizzo,))

        # Log the deletion
        log(type='info', 
            message=f'User {request.user_identity} deleted address', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        return create_response(message={'outcome': 'address successfully deleted'}, status_code=STATUS_CODES["ok"])

class AddressUpdate(Resource):
    @jwt_required_endpoint
    def patch(self):
        # Gather parameters
        idIndirizzo = int(request.args.get('idIndirizzo'))
        toModify = request.args.get('toModify')
        newValue = request.args.get('newValue')

        # Check if the field to modify is allowed
        if toModify in ['idIndirizzo']:
            return create_response(message={'outcome': 'error, specified field cannot be modified'}, status_code=403)

        # Check if address exists
        address = fetchone_query('SELECT * FROM indirizzi WHERE idIndirizzo = %s', (idIndirizzo,))
        if address is None:
            return create_response(message={'outcome': 'error, specified address does not exist'}, status_code=STATUS_CODES["not_found"])

        # Update the address
        execute_query(f'UPDATE indirizzi SET {toModify} = %s WHERE idIndirizzo = %s', (newValue, idIndirizzo))

        # Log the update
        log(type='info', 
            message=f'User {request.user_identity} updated address', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        return create_response(message={'outcome': 'address successfully updated'}, status_code=STATUS_CODES["ok"])

class AddressRead(Resource):
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
        outcome = validate_filters(data=data, table_name='indirizzi')
        if outcome != True:  # if the validation fails, outcome will be a dict with the error message
            return outcome, STATUS_CODES["bad_request"]

        try:
            # Build the query
            query, params = build_query_from_filters(data=data, table_name='indirizzi', limit=limit, offset=offset)

            # Execute query
            addresses = fetchall_query(query, tuple(params))

            # Log the read
            log(type='info', 
                message=f'User {request.user_identity} read addresses with filters: {data}', 
                origin_name=API_SERVER_NAME_IN_LOG, 
                origin_host=API_SERVER_HOST, 
                origin_port=API_SERVER_PORT)

            return create_response(message=addresses, status_code=STATUS_CODES["ok"])
        except Exception as err:
            return create_response(message={'error': str(err)}, status_code=STATUS_CODES["internal_error"])

# Add resources to the API
api.add_resource(AddressRegister, '/register')
api.add_resource(AddressDelete, '/delete')
api.add_resource(AddressUpdate, '/update')
api.add_resource(AddressRead, '/read')