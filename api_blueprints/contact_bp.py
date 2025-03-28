from flask import Blueprint, request, make_response, jsonify
from flask_restful import Api, Resource
import mysql.connector
from config import API_SERVER_HOST, API_SERVER_PORT, API_SERVER_NAME_IN_LOG
from .blueprints_utils import validate_filters, build_query_from_filters, fetchone_query, fetchall_query, execute_query, log, jwt_required_endpoint

contact_bp = Blueprint('contact', __name__)
api = Api(contact_bp)

class ContactRegister(Resource):
    @jwt_required_endpoint
    def post(self):
        params = {
            'nome': request.args.get('nome'),
            'cognome': request.args.get('cognome'),
            'telefono': request.args.get('telefono'),
            'email': request.args.get('email'),
            'ruolo': request.args.get('ruolo'),
            'idAzienda': int(request.args.get('idAzienda'))
        }

        if not fetchone_query('SELECT * FROM aziende WHERE idAzienda = %s', (params['idAzienda'],)):
            return make_response(jsonify({'outcome': 'Company not found'}), 404)

        try:
            execute_query(
                '''INSERT INTO contatti 
                (nome, cognome, telefono, email, ruolo, idAzienda)
                VALUES (%s, %s, %s, %s, %s, %s)''',
                tuple(params.values())
            )
            log(type='info', message=f'User {request.user_identity} created contact',
                origin_name=API_SERVER_NAME_IN_LOG, origin_host=API_SERVER_HOST, origin_port=API_SERVER_PORT)
            return make_response(jsonify({'outcome': 'Contact created'}), 201)
        except mysql.connector.IntegrityError:
            return make_response(jsonify({'outcome': 'Contact already exists'}), 400)

class ContactDelete(Resource):
    @jwt_required_endpoint
    def delete(self):
        contact_id = int(request.args.get('idContatto'))
        if not fetchone_query('SELECT * FROM contatti WHERE idContatto = %s', (contact_id,)):
            return make_response(jsonify({'outcome': 'Contact not found'}), 404)
            
        execute_query('DELETE FROM contatti WHERE idContatto = %s', (contact_id,))
        
        log(type='info', message=f'User {request.user_identity} deleted contact',
            origin_name=API_SERVER_NAME_IN_LOG, origin_host=API_SERVER_HOST, origin_port=API_SERVER_PORT)
        
        return make_response(jsonify({'outcome': 'contact successfully deleted'}), 200)

class ContactUpdate(Resource):
    allowed_fields = ['nome', 'cognome', 'telefono', 'email', 'ruolo', 'idAzienda']
    
    @jwt_required_endpoint
    def patch(self):
        contact_id = int(request.args.get('idContatto'))
        field = request.args.get('toModify')
        value = request.args.get('newValue')

        if field not in self.allowed_fields:
            return make_response(jsonify({'outcome': 'Invalid field'}), 400)

        if not fetchone_query('SELECT * FROM contatti WHERE idContatto = %s', (contact_id,)):
            return make_response(jsonify({'outcome': 'Contact not found'}), 404)

        if field == 'telefono':
            value = int(value)

        execute_query(f'UPDATE contatti SET {field} = %s WHERE idContatto = %s', (value, contact_id))
        
        log(type='info', message=f'User {request.user_identity} updated contact',
            origin_name=API_SERVER_NAME_IN_LOG, origin_host=API_SERVER_HOST, origin_port=API_SERVER_PORT)
        
        return make_response(jsonify({'outcome': 'contact successfully updated'}), 200)

class ContactRead(Resource):
    @jwt_required_endpoint
    def get(self):
        try:
            limit = int(request.args.get('limit', 10))
            offset = int(request.args.get('offset', 0))
        except (ValueError, TypeError) as ex:
            return make_response(jsonify({'error': f'invalid limit or offset value: {ex}'}), 400)

        data = request.get_json()
        if (validation := validate_filters(data, 'contatti')) is not True:
            return validation, 400

        try:
            query, params = build_query_from_filters(
                data=data, table_name='contatti',
                limit=limit, offset=offset
            )
            
            contacts = [dict(row) for row in fetchall_query(query, tuple(params))]
            
            return make_response(jsonify(contacts), 200)
        except Exception as err:
            return make_response(jsonify({'error': str(err)}), 500)

api.add_resource(ContactRegister, '/register')
api.add_resource(ContactDelete, '/delete')
api.add_resource(ContactUpdate, '/update')
api.add_resource(ContactRead, '/read')