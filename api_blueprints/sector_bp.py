from os.path import basename as os_path_basename
from flask import Blueprint, request, Response
from flask_restful import Api, Resource
from flask_jwt_extended import get_jwt_identity
from mysql.connector import IntegrityError
from typing import Dict, Union, List, Any
from .blueprints_utils import (check_authorization, fetchone_query, 
                               fetchall_query, execute_query, 
                               log, jwt_required_endpoint, 
                               create_response, has_valid_json,
                               is_input_safe, get_class_http_verbs)
from config import (API_SERVER_HOST, API_SERVER_PORT, 
                    API_SERVER_NAME_IN_LOG, STATUS_CODES)

# Define constants
BP_NAME = os_path_basename(__file__).replace('_bp.py', '')

# Create the blueprint and API
sector_bp = Blueprint(BP_NAME, __name__)
api = Api(sector_bp)

class Sector(Resource):
    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin'])
    def post(self) -> Response:
        """
        Create a new sector.
        The request body must be a JSON object with application/json content type.
        """

        # Validate request
        data: Union[str, Dict[str, Any]] = has_valid_json(request)
        if isinstance(data, str): 
            return create_response(message={'error': data}, status_code=STATUS_CODES["bad_request"])

        # Check for sql injection
        if not is_input_safe(data):
            return create_response(message={'error': 'invalid input, suspected sql injection'}, status_code=STATUS_CODES["bad_request"])

        # Gather parameters
        settore: str = data.get('settore')

        # Validate parameters
        if settore is None or len(settore) == 0:
            return create_response(message={'error': 'settore parameter is required'}, status_code=STATUS_CODES["bad_request"])
        elif len(settore) > 255:
            return create_response(message={'error': 'settore parameter is too long'}, status_code=STATUS_CODES["bad_request"])
        elif not isinstance(settore, str):
            return create_response(message={'error': 'settore parameter must be a string'}, status_code=STATUS_CODES["bad_request"])
        
        try:
            # Insert the sector
            lastrowid: int = execute_query('INSERT INTO settori (settore) VALUES (%s)', (settore,))
        except IntegrityError as ex: 
            log(type='error',
                message=f'User {get_jwt_identity().get("email")} tried to create sector {settore} but it generated {ex}',
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                origin_port=API_SERVER_PORT)
            return create_response(message={'error': 'conflict error'}, status_code=STATUS_CODES["conflict"])
        except Exception as ex:
            log(type='error',
                message=f'User {get_jwt_identity().get("email")} failed to create sector {settore} with error: {str(ex)}',
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                origin_port=API_SERVER_PORT)
            return create_response(message={'error': "internal server error"}, status_code=STATUS_CODES["internal_error"])

        # Log the sector creation
        log(type='info',
            message=f'User {get_jwt_identity().get("email")} created sector {settore}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        # Return a success message
        return create_response(message={'outcome': 'sector successfully created',
                                        'location': f'http://{API_SERVER_HOST}:{API_SERVER_PORT}/api/{BP_NAME}/{lastrowid}'}, status_code=STATUS_CODES["created"])

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin'])
    def delete(self, settore) -> Response:
        """
        Delete a sector.
        The request must include the sector name as a path variable.
        """
        
        # Check if sector exists
        sector: Dict[str, Any] = fetchone_query('SELECT * FROM settori WHERE settore = %s', (settore,))
        if sector is None:
            return {'outcome': 'error, specified sector does not exist'}, STATUS_CODES["not_found"]

        # Delete the sector
        execute_query('DELETE FROM settori WHERE settore = %s', (settore,))

        # Log the deletion
        log(type='info',
            message=f'User {get_jwt_identity().get("email")} deleted sector {settore}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        # Return a success message
        return create_response(message={'outcome': 'sector successfully deleted'}, status_code=STATUS_CODES["no_content"])

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin'])
    def patch(self, settore) -> Response:
        """
        Update a sector.
        The request must include the sector name as a path variable.
        """

        # Validate request
        data: Union[str, Dict[str, Any]] = has_valid_json(request)
        if isinstance(data, str): 
            return create_response(message={'error': data}, status_code=STATUS_CODES["bad_request"])

        # Check for sql injection
        if not is_input_safe(data):
            return create_response(message={'error': 'invalid input, suspected sql injection'}, status_code=STATUS_CODES["bad_request"])

        # Gather JSON data
        newValue: str = data.get('newValue')

        # Validate parameters
        if newValue is None or len(newValue) == 0:
            return create_response(message={'error': 'newValue parameter is required'}, status_code=STATUS_CODES["bad_request"])

        # Check if sector exists
        sector: Dict[str, Any] = fetchone_query('SELECT * FROM settori WHERE settore = %s', (settore,))
        if sector is None:
            return create_response(message={'outcome': 'error, specified sector does not exist'}, status_code=STATUS_CODES["not_found"])

        # Update the sector
        execute_query('UPDATE settori SET settore = %s WHERE settore = %s', (newValue, settore))

        # Log the update
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} updated sector {settore}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        # Return a success message
        return create_response(message={'outcome': 'sector successfully updated'}, status_code=STATUS_CODES["ok"])

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor', 'teacher'])
    def get(self) -> Response:
        """
        Get all sectors with pagination.
        The request can include limit and offset as query parameters.
        """

        # Gather URL parameters
        try: 
            limit: int = int(request.args.get('limit')) if request.args.get('limit') else 10 # Default to 10
            offset: int = int(request.args.get('offset')) if request.args.get('offset') else 0 # Default to 0
        except (ValueError, TypeError) as ex:
            return create_response(message={'error': f'invalid limit or offset parameter: {ex}'}, status_code=STATUS_CODES["bad_request"])

        # This endpoint does not require filters as the table has only one column 

        try:
            # Execute query
            sectors: List[Dict[str, Any]] = fetchall_query('SELECT settore FROM settori LIMIT %s OFFSET %s', (limit, offset))

            # Log the read
            log(type='info', 
                message=f'User {get_jwt_identity().get("email")} read all sectors', 
                origin_name=API_SERVER_NAME_IN_LOG, 
                origin_host=API_SERVER_HOST, 
                origin_port=API_SERVER_PORT)

            # Return result
            return create_response(message=sectors, status_code=STATUS_CODES["ok"])
        except Exception as err:
            return create_response(message={'error': str(err)}, status_code=STATUS_CODES["internal_error"])

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor', 'teacher'])
    def options(self) -> Response:
        # Define allowed methods
        allowed_methods = get_class_http_verbs(type(self))
        
        # Create the response
        response = Response(status=STATUS_CODES["ok"])
        response.headers['Allow'] = ', '.join(allowed_methods)
        response.headers['Access-Control-Allow-Origin'] = '*'  # Adjust as needed for CORS
        response.headers['Access-Control-Allow-Methods'] = ', '.join(allowed_methods)
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        
        return response

api.add_resource(Sector, f'/{BP_NAME}', f'{BP_NAME}/<string:settore>')
