from flask import Blueprint, jsonify, request
from flask_restful import Api, Resource
import mysql.connector
from config import API_SERVER_HOST, API_SERVER_PORT, API_SERVER_NAME_IN_LOG
from utils import fetchone_query, execute_query, log, jwt_required_endpoint

# Create the blueprint and API
contact_bp = Blueprint('contact', __name__)
api = Api(contact_bp)

class ContactRegister(Resource):
    @jwt_required_endpoint
    def post(self):
        # Gather parameters
        nome = request.args.get('nome')
        cognome = request.args.get('cognome')
        telefono = request.args.get('telefono')
        email = request.args.get('email')
        ruolo = request.args.get('ruolo')
        idAzienda = int(request.args.get('idAzienda'))

        # Check if idAzienda exists
        company = fetchone_query('SELECT * FROM aziende WHERE idAzienda = %s', (idAzienda,))
        if company is None:
            return jsonify({'outcome': 'error, specified company does not exist'})

        # Insert the contact
        execute_query(
            'INSERT INTO contatti (nome, cognome, telefono, email, ruolo, idAzienda) VALUES (%s, %s, %s, %s, %s, %s)',
            (nome, cognome, telefono, email, ruolo, idAzienda)
        )

        # Log the contact creation
        log(type='info', 
            message=f'User {request.user_identity} created contact', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        return jsonify({'outcome': 'success, contact inserted'}), 201

class ContactDelete(Resource):
    @jwt_required_endpoint
    def delete(self):
        # Gather parameters
        idContatto = int(request.args.get('idContatto'))

        # Check if contact exists
        contact = fetchone_query('SELECT * FROM contatti WHERE idContatto = %s', (idContatto,))
        if contact is None:
            return jsonify({'outcome': 'error, specified contact does not exist'})

        # Delete the contact
        execute_query('DELETE FROM contatti WHERE idContatto = %s', (idContatto,))

        # Log the deletion
        log(type='info',
            message= f'User {request.user_identity} deleted contact', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        return jsonify({'outcome': 'contact successfully deleted'})

class ContactUpdate(Resource):
    @jwt_required_endpoint
    def patch(self):
        # Gather parameters
        idContatto = int(request.args.get('idContatto'))
        toModify = request.args.get('toModify')
        newValue = request.args.get('newValue')

        # Check if the field to modify is allowed
        if toModify in ['idContatto']:
            return jsonify({'outcome': 'error, specified field cannot be modified'})

        # Check if any casting operations are needed
        if toModify in ['telefono']:
            newValue = int(newValue)

        # Check if contact exists
        contact = fetchone_query('SELECT * FROM contatti WHERE idContatto = %s', (idContatto,))
        if contact is None:
            return jsonify({'outcome': 'error, specified contact does not exist'})

        # Update the contact
        execute_query(f'UPDATE contatti SET {toModify} = %s WHERE idContatto = %s', (newValue, idContatto))

        # Log the update
        log(type='info',
            message= f'User {request.user_identity} updated contact', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        return jsonify({'outcome': 'contact successfully updated'})

class ContactRead(Resource):
    @jwt_required_endpoint
    def get(self):
        # Gather parameters
        try:
            idContatto = int(request.args.get('idContatto'))
        except (ValueError, TypeError):
            return jsonify({'error': 'invalid idContatto parameter'}), 400

        # Execute query
        try:
            contact = fetchone_query('SELECT * FROM contatti WHERE idContatto = %s', (idContatto,))

            # Log the read
            log(type='info',
                message=f'User {request.user_identity} read contact', 
                origin_name=API_SERVER_NAME_IN_LOG, 
                origin_host=API_SERVER_HOST, 
                origin_port=API_SERVER_PORT)

            return jsonify(contact), 200
        except mysql.connector.Error as err:
            return jsonify({'error': str(err)}), 500

# Add resources to the API
api.add_resource(ContactRegister, '/register')
api.add_resource(ContactDelete, '/delete')
api.add_resource(ContactUpdate, '/update')
api.add_resource(ContactRead, '/read')