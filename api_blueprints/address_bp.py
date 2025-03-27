from flask import Blueprint, jsonify, request
from flask_restful import Api, Resource
from config import API_SERVER_HOST, API_SERVER_PORT, API_SERVER_NAME_IN_LOG
import mysql.connector
from utils import fetchone_query, execute_query, log, jwt_required_endpoint
from blueprints_utils import validate_filters
import json

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
            return jsonify({'outcome': 'error, specified company does not exist'})

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

        return jsonify({'outcome': 'address successfully created'}), 201

class AddressDelete(Resource):
    @jwt_required_endpoint
    def delete(self):
        # Gather parameters
        idIndirizzo = int(request.args.get('idIndirizzo'))

        # Check if address exists
        address = fetchone_query('SELECT * FROM indirizzi WHERE idIndirizzo = %s', (idIndirizzo,))
        if address is None:
            return jsonify({'outcome': 'error, specified address does not exist'})

        # Delete the address
        execute_query('DELETE FROM indirizzi WHERE idIndirizzo = %s', (idIndirizzo,))

        # Log the deletion
        log(type='info', 
            message=f'User {request.user_identity} deleted address', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        return jsonify({'outcome': 'address successfully deleted'})

class AddressUpdate(Resource):
    @jwt_required_endpoint
    def patch(self):
        # Gather parameters
        idIndirizzo = int(request.args.get('idIndirizzo'))
        toModify = request.args.get('toModify')
        newValue = request.args.get('newValue')

        # Check if the field to modify is allowed
        if toModify in ['idIndirizzo']:
            return jsonify({'outcome': 'error, specified field cannot be modified'})

        # Check if address exists
        address = fetchone_query('SELECT * FROM indirizzi WHERE idIndirizzo = %s', (idIndirizzo,))
        if address is None:
            return jsonify({'outcome': 'error, specified address does not exist'})

        # Update the address
        execute_query(f'UPDATE indirizzi SET {toModify} = %s WHERE idIndirizzo = %s', (newValue, idIndirizzo))

        # Log the update
        log(type='info', 
            message=f'User {request.user_identity} updated address', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        return jsonify({'outcome': 'address successfully updated'})

class AddressRead(Resource):
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
        outcome = validate_filters(data=data, table_name='indirizzi')
        if outcome is not None: 
            return outcome
        

        with open('../table_metadata.json') as metadata_file:
            try:
                metadata = json.load(metadata_file)
                indirizzi_available_filters = metadata.get('indirizzi', [])
                if not isinstance(indirizzi_available_filters, list) or not all(isinstance(item, str) for item in indirizzi_available_filters):
                    return jsonify({'error': 'invalid indirizzi column values in metadata'}), 400
                
                # Get list of keys in data json
                filters_key = list(data.keys()) if isinstance(data, dict) else []

                # Check if any filter key is not in indirizzi_filters
                invalid_filters = [key for key in filters_key if key not in indirizzi_available_filters]
                if invalid_filters:
                    return jsonify({'error': f'Invalid filter(s): {", ".join(invalid_filters)}'}), 400

            except json.JSONDecodeError:
                return jsonify({'error': 'failed to parse metadata file'}), 500

        try:
            # Build the query
            filters = " AND ".join([f"{key} = %s" for key in filters_key])
            query = f"SELECT * FROM indirizzi WHERE {filters} LIMIT %s OFFSET %s" if filters else "SELECT * FROM indirizzi LIMIT %s OFFSET %s"
            params = [data[key] for key in filters_key] + [limit, offset]

            # Execute query
            address = fetchone_query(query, tuple(params))

            # Log the read
            log(type='info', 
                message=f'User {request.user_identity} read address', 
                origin_name=API_SERVER_NAME_IN_LOG, 
                origin_host=API_SERVER_HOST, 
                origin_port=API_SERVER_PORT)

            return jsonify(address), 200
        except mysql.connector.Error as err:
            return jsonify({'error': str(err)}), 500

# Add resources to the API
api.add_resource(AddressRegister, '/register')
api.add_resource(AddressDelete, '/delete')
api.add_resource(AddressUpdate, '/update')
api.add_resource(AddressRead, '/read')