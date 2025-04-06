from os.path import basename as os_path_basename
from flask import Blueprint, request, Response
from flask_restful import Api, Resource
from flask_jwt_extended import get_jwt_identity
from config import API_SERVER_HOST, API_SERVER_PORT, API_SERVER_NAME_IN_LOG, STATUS_CODES
from mysql.connector import IntegrityError
from .blueprints_utils import (check_authorization, fetchone_query, 
                               fetchall_query, execute_query, 
                               log, jwt_required_endpoint, 
                               create_response)

# Define constants
BP_NAME = os_path_basename(__file__).replace('_bp.py', '')

# Create the blueprint and API
legalform_bp = Blueprint(BP_NAME, __name__)
api = Api(legalform_bp)

class LegalForm(Resource):
    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor'])
    def post(self) -> Response:
        """
        Create a new legal form.
        The request must contain a JSON body with application/json.
        """
        # Ensure the request has a JSON body
        if not request.is_json or request.json is None:
            return create_response(message={'error': 'Request body must be valid JSON with Content-Type: application/json'}, status_code=STATUS_CODES["bad_request"])

        # Gather parameters
        forma = request.json.get('forma')
        if forma is None or not isinstance(forma, str) or len(forma) == 0:
            return create_response(message={'error': 'Invalid legal form'}, status_code=STATUS_CODES["bad_request"])

        try:
            # Insert the legal form
            execute_query('INSERT INTO formaGiuridica (forma) VALUES (%s)', (forma,))
        except IntegrityError: 
            log(type='error',
                message=f'User {get_jwt_identity().get("email")} tried to create legal form {forma} but it already existed',
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                origin_port=API_SERVER_PORT)
            return create_response(message={'outcome': 'error, specified legal form already exists'}, status_code=STATUS_CODES["conflict"])
        except Exception as ex:
            log(type='error',
                message=f'User {get_jwt_identity().get("email")} failed to create legal form {forma} with error: {str(ex)}',
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                origin_port=API_SERVER_PORT)
            return create_response(message={'error': "internal server error"}, status_code=STATUS_CODES["internal_error"])

        # Log the legal form creation
        log(type='info',
            message=f'User {get_jwt_identity().get("email")} created legal form {forma}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        # Return a success message
        return create_response(message={'outcome': 'legal form successfully created',
                                        'location': f'http://{API_SERVER_HOST}:{API_SERVER_PORT}/api/{BP_NAME}/{forma}'}, status_code=STATUS_CODES["created"])

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor'])
    def delete(self, forma) -> Response:
        """
        Delete a legal form.
        The legal form is passed as a path variable.
        """
        # Delete the legal form
        execute_query('DELETE FROM formaGiuridica WHERE forma = %s', (forma,))

        # Log the deletion
        log(type='info',
            message=f'User {get_jwt_identity().get("email")} deleted legal form {forma}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        # Return a success message
        return create_response(message={'outcome': 'legal form successfully deleted'}, status_code=STATUS_CODES["no_content"])

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor'])
    def patch(self, forma) -> Response:
        """
        Update a legal form.
        The legal form is passed as a path variable.
        """
        # Gather parameters
        newValue = request.args.get('newValue')

        # Check if legal form exists
        form = fetchone_query('SELECT * FROM formaGiuridica WHERE forma = %s', (forma,))
        if form is None:
            return create_response(message={'outcome': 'error, specified legal form does not exist'}, status_code=STATUS_CODES["not_found"])

        # Update the legal form
        execute_query('UPDATE formaGiuridica SET forma = %s WHERE forma = %s', (newValue, forma))

        # Log the update
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} updated legal form {forma} to {newValue}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        # Return a success message
        return create_response(message={'outcome': 'legal form successfully updated'}, status_code=STATUS_CODES["ok"])

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor', 'teacher'])
    def get(self) -> Response:
        """
        Get all legal forms.
        The results are paginated with limit and offset parameters.
        """
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
                message=f'User {get_jwt_identity().get("email")} read all legal forms', 
                origin_name=API_SERVER_NAME_IN_LOG, 
                origin_host=API_SERVER_HOST, 
                origin_port=API_SERVER_PORT)

            # Return the result
            return create_response(message=forms, status_code=STATUS_CODES["ok"])
        except Exception as err:
            return create_response(message={'error': str(err)}, status_code=STATUS_CODES["internal_error"])

api.add_resource(LegalForm, f'/{BP_NAME}', f'{BP_NAME}/<string:forma>')