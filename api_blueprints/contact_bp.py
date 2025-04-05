from flask import Blueprint, request
from flask_restful import Api, Resource
from flask_jwt_extended import get_jwt_identity
from config import API_SERVER_HOST, API_SERVER_PORT, API_SERVER_NAME_IN_LOG, STATUS_CODES
from .blueprints_utils import (check_authorization, validate_filters, 
                               build_select_query_from_filters, fetchone_query, 
                               fetchall_query, execute_query, 
                               log, jwt_required_endpoint, 
                               create_response, build_update_query_from_filters)

contact_bp = Blueprint('contact', __name__)
api = Api(contact_bp)

class Contact(Resource):
    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor'])
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
            return create_response(message={'outcome': 'Company not found'}, status_code=STATUS_CODES["not_found"])

        try:
            # Execute query to insert the contact
            lastrowid: int = execute_query(
                '''INSERT INTO contatti 
                (nome, cognome, telefono, email, ruolo, idAzienda)
                VALUES (%s, %s, %s, %s, %s, %s)''',
                tuple(params.values())
            )
            
            # Log the creation of the contact
            log(type='info', 
                message=f'User {get_jwt_identity().get("email")} created contact {lastrowid}',
                origin_name=API_SERVER_NAME_IN_LOG, 
                origin_host=API_SERVER_HOST, 
                origin_port=API_SERVER_PORT)
            
            # Return a success message
            return create_response(message={'outcome': 'contact created'}, status_code=STATUS_CODES["created"])
        except Exception as err:
            return create_response(message={'outcome': 'contact already exists'}, status_code=STATUS_CODES["bad_request"])

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor'])
    def delete(self):
        # Gather parameters
        try:
            contact_id = int(request.args.get('idContatto'))
        except (ValueError, TypeError):
            return create_response(message={'outcome': 'invalid contact ID'}, status_code=STATUS_CODES["bad_request"])
        
        # Execute query to delete the contact    
        execute_query('DELETE FROM contatti WHERE idContatto = %s', (contact_id,))
        
        # Log the deletion of the contact
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} deleted contact {contact_id}',
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST,
            origin_port=API_SERVER_PORT)
        
        # Return a success message
        return create_response(message={'outcome': 'contact successfully deleted'}, status_code=STATUS_CODES["no_content"])

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor'])
    def patch(self):
        # Gather parameters
        toModify = request.args.get('toModify')
        newValues = request.args.get('newValue')
        try:
            contact_id = int(request.args.get('idContatto'))
        except (ValueError, TypeError):
            return create_response(message={'outcome': 'invalid contact ID'}, status_code=STATUS_CODES["bad_request"])

        # Validate parameters
        if len(toModify) != len(newValues):
            return create_response(message={'outcome': 'Mismatched fields and values lists lengths'}, status_code=STATUS_CODES["bad_request"])

        # Build a dictionary with fields as keys and values as values
        updates = dict(zip(toModify, newValues))  # {field1: value1, field2: value2, ...}

        # Check that the specified fields can be modified
        not_allowed_fields = ['idContatto']
        for field in toModify:
            if field in not_allowed_fields:
                return create_response(message={'outcome': f'error, field "{field} cannot be modified"'}, status_code=STATUS_CODES["bad_request"])

        # Check that the specified fields actually exist in the database
        outcome = validate_filters(toModify, 'contatti')
        if outcome is not True:
            return create_response(message=outcome, status_code=STATUS_CODES["bad_request"])

        # Check that the specified contact exists
        contact = fetchone_query('SELECT * FROM contatti WHERE idContatto = %s', (contact_id,))
        if not contact:
            return create_response(message={'outcome': 'specified contact not found'}, status_code=STATUS_CODES["not_found"])

        # Build the update query
        query, params = build_update_query_from_filters(
            data=updates, table_name='contatti', 
            id=contact_id
        )

        # Execute the update query
        execute_query(query, params)
        
        # Log the update of the contact
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} updated contact {contact_id}',
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)
        
        # Return a success message
        return create_response(message={'outcome': 'contact successfully updated'}, status_code=STATUS_CODES["ok"])

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor', 'teacher'])
    def get(self, id=None):
        # Gather parameters
        nome = request.args.get('nome')
        cognome = request.args.get('cognome')
        telefono = request.args.get('telefono')
        email = request.args.get('email')
        ruolo = request.args.get('ruolo')
        try:
            idAzienda = int(request.args.get('idAzienda')) if request.args.get('idAzienda') else None
        except (ValueError, TypeError):
            return create_response(message={'outcome': 'invalid company ID'}, status_code=STATUS_CODES["bad_request"])
        try:
            limit = int(request.args.get('limit', 10))  # Default limit to 10 if not provided
            offset = int(request.args.get('offset', 0))  # Default offset to 0 if not provided
        except (ValueError, TypeError):
            return create_response(message={'error': 'Invalid limit or offset values'}, status_code=STATUS_CODES["bad_request"])

        # Build the filters dictionary (only include non-null values)
        filters = {key: value for key, value in {
            "idContatto": id,  # Use the path variable 'id'
            "nome": nome,
            "cognome": cognome,
            "telefono": telefono,
            "email": email,
            "ruolo": ruolo,
            "idAzienda": idAzienda
        }.items() if value}

        try:
            # Build the select query
            query, params = build_select_query_from_filters(
                data=filters, table_name='contatti',
                limit=limit, offset=offset
            )

            # Execute the query
            contacts = fetchall_query(query, params)

            # Get the ids to log
            ids = [contact['idContatto'] for contact in contacts]

            # Log the read operation
            log(type='info', 
                message=f'User {get_jwt_identity().get("email")} read contacts {ids}',
                origin_name=API_SERVER_NAME_IN_LOG, 
                origin_host=API_SERVER_HOST, 
                origin_port=API_SERVER_PORT
            )

            # Return the contacts
            return create_response(message=contacts, status_code=STATUS_CODES["ok"])
        except Exception as err:
            return create_response(message={'error': str(err)}, status_code=STATUS_CODES["internal_error"]) 

api.add_resource(Contact, '/contact', '/contact/<int:id>')