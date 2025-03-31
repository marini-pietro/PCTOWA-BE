from flask import Blueprint, request, make_response, jsonify
from flask_restful import Api, Resource
from config import API_SERVER_HOST, API_SERVER_PORT, API_SERVER_NAME_IN_LOG
from .blueprints_utils import validate_filters, validate_inputs, build_query_from_filters, fetchone_query, fetchall_query, execute_query, log, jwt_required_endpoint

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
            return make_response(jsonify({'outcome': 'error, specified company does not exist'}), 404)

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

        return make_response(jsonify({'outcome': 'address successfully created'}), 201)

class AddressDelete(Resource):
    @jwt_required_endpoint
    def delete(self):
        # Gather parameters
        idIndirizzo = int(request.args.get('idIndirizzo'))

        # Check if address exists
        address = fetchone_query('SELECT * FROM indirizzi WHERE idIndirizzo = %s', (idIndirizzo,))
        if address is None:
            return make_response(jsonify({'outcome': 'error, specified address does not exist'}), 404)

        # Delete the address
        execute_query('DELETE FROM indirizzi WHERE idIndirizzo = %s', (idIndirizzo,))

        # Log the deletion
        log(type='info', 
            message=f'User {request.user_identity} deleted address', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        return make_response(jsonify({'outcome': 'address successfully deleted'}), 200)

class AddressUpdate(Resource):
    @jwt_required_endpoint
    def patch(self):
        # Gather parameters
        idIndirizzo = int(request.args.get('idIndirizzo'))
        toModify = request.args.get('toModify')
        newValue = request.args.get('newValue')

        # Check if the field to modify is allowed
        if toModify in ['idIndirizzo']:
            return make_response(jsonify({'outcome': 'error, specified field cannot be modified'}), 403)

        # Check if address exists
        address = fetchone_query('SELECT * FROM indirizzi WHERE idIndirizzo = %s', (idIndirizzo,))
        if address is None:
            return make_response(jsonify({'outcome': 'error, specified address does not exist'}), 404)

        # Update the address
        execute_query(f'UPDATE indirizzi SET {toModify} = %s WHERE idIndirizzo = %s', (newValue, idIndirizzo))

        # Log the update
        log(type='info', 
            message=f'User {request.user_identity} updated address', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        return make_response(jsonify({'outcome': 'address successfully updated'}), 200)

class AddressRead(Resource):
    @jwt_required_endpoint
    def get(self):
        # Gather URL parameters
        try:
            limit = int(request.args.get('limit'))
            offset = int(request.args.get('offset'))
        except (ValueError, TypeError):
            return make_response(jsonify({'error': 'invalid limit or offset parameter'}), 400)

        # Gather json filters
        data = request.get_json()

        # Validate filters
        outcome = validate_filters(data=data, table_name='indirizzi')
        if outcome != True:  # if the validation fails, outcome will be a dict with the error message
            return outcome, 400

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

            return make_response(jsonify(addresses), 200)
        except Exception as err:
            return make_response(jsonify({'error': str(err)}), 500)

# Add resources to the API
api.add_resource(AddressRegister, '/register')
api.add_resource(AddressDelete, '/delete')
api.add_resource(AddressUpdate, '/update')
api.add_resource(AddressRead, '/read')