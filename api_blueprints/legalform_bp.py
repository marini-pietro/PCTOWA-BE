from flask import Blueprint, request
from flask_restful import Api, Resource
from config import API_SERVER_HOST, API_SERVER_PORT, API_SERVER_NAME_IN_LOG, STATUS_CODES
from .blueprints_utils import (check_authorization, fetchone_query, 
                               fetchall_query, execute_query, 
                               log, jwt_required_endpoint, 
                               create_response)

# Create the blueprint and API
legalform_bp = Blueprint('legalform', __name__)
api = Api(legalform_bp)

class LegalFormRegister(Resource):
    @jwt_required_endpoint
    def post(self):
        # Gather parameters
        legalform = request.args.get('forma')

        # Check if legal form already exists
        form = fetchone_query('SELECT * FROM formaGiuridica WHERE forma = %s', (legalform,))
        if form is not None:
            return {'outcome': 'error, specified legal form already exists'}, 403

        # Insert the legal form
        lastrowid = execute_query('INSERT INTO formaGiuridica (forma) VALUES (%s)', (legalform,))

        # Log the legal form creation
        log(type='info',
            message=f'User {request.user_identity} created legal form {lastrowid}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        # Return a success message
        return create_response(message={'outcome': 'legal form successfully created'}, status_code=STATUS_CODES["created"])

class LegalFormDelete(Resource):
    @jwt_required_endpoint
    def delete(self):
        # Gather parameters
        legalform = request.args.get('forma')

        # Delete the legal form
        execute_query('DELETE FROM formaGiuridica WHERE forma = %s', (legalform,))

        # Log the deletion
        log(type='info',
            message=f'User {request.user_identity} deleted legal form {legalform}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        # Return a success message
        return create_response(message={'outcome': 'legal form successfully deleted'}, status_code=STATUS_CODES["no_content"])

class LegalFormUpdate(Resource):
    @jwt_required_endpoint
    def patch(self):
        # Gather parameters
        legalform = request.args.get('forma')
        newValue = request.args.get('newValue')

        # Check if legal form exists
        form = fetchone_query('SELECT * FROM formaGiuridica WHERE forma = %s', (legalform,))
        if form is None:
            return create_response(message={'outcome': 'error, specified legal form does not exist'}, status_code=STATUS_CODES["not_found"])

        # Update the legal form
        execute_query('UPDATE formaGiuridica SET forma = %s WHERE forma = %s', (newValue, legalform))

        # Log the update
        log(type='info', 
            message=f'User {request.user_identity} updated legal form {legalform} to {newValue}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        # Return a success message
        return create_response(message={'outcome': 'legal form successfully updated'}, status_code=STATUS_CODES["ok"])

class LegalFormRead(Resource):
    @jwt_required_endpoint
    def get(self):
        # Gather URL parameters
        try:
            limit = int(request.args.get('limit'))
            offset = int(request.args.get('offset'))
        except (ValueError, TypeError) as ex:
            return create_response(message={'error': f'invalid limit or offset parameter: {ex}'}, status_code=STATUS_CODES["bad_request"])

        # This endpoint does not require filters as the table has only one column 

        try:
            # Build the query
            query, params = 'SELECT forma FROM formaGiuridica LIMIT %s OFFSET %s', (limit, offset)

            # Execute query
            forms = fetchall_query(query, tuple(params))

            # Log the read
            log(type='info', 
                message=f'User {request.user_identity} read all legal forms', 
                origin_name=API_SERVER_NAME_IN_LOG, 
                origin_host=API_SERVER_HOST, 
                origin_port=API_SERVER_PORT)

            # Return the result
            return create_response(message=forms, status_code=STATUS_CODES["ok"])
        except Exception as err:
            return create_response(message={'error': str(err)}, status_code=STATUS_CODES["internal_error"])

# Add resources to the API
api.add_resource(LegalFormRegister, '/register')
api.add_resource(LegalFormDelete, '/delete')
api.add_resource(LegalFormUpdate, '/update')
api.add_resource(LegalFormRead, '/read')