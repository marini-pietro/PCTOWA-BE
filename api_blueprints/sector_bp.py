from flask import Blueprint, request
from flask_restful import Api, Resource
from flask_jwt_extended import get_jwt_identity
from config import API_SERVER_HOST, API_SERVER_PORT, API_SERVER_NAME_IN_LOG, STATUS_CODES
from .blueprints_utils import (check_authorization, fetchone_query, 
                               fetchall_query, execute_query, 
                               log, jwt_required_endpoint, 
                               create_response)

# Create the blueprint and API
sector_bp = Blueprint('sector', __name__)
api = Api(sector_bp)

class Sector(Resource):
    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin'])
    def post(self):
        # Gather parameters
        settore = request.args.get('settore')

        # Check if sector exists
        sector = fetchone_query('SELECT * FROM settori WHERE settore = %s', (settore,))
        if sector is not None:
            return {'outcome': 'error, specified sector already exists'}, 403

        # Insert the sector
        lastrowid = execute_query('INSERT INTO settori (settore) VALUES (%s)', (settore,))

        # Log the sector creation
        log(type='info',
            message=f'User {get_jwt_identity().get("email")} created sector {settore}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)

        # Return a success message
        return create_response(message={'outcome': 'sector successfully created',
                                        'location': f'http://{API_SERVER_HOST}:{API_SERVER_PORT}/api/sector/{lastrowid}'}, status_code=STATUS_CODES["created"])

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin'])
    def delete(self):
        # Gather parameters
        settore = request.args.get('settore')

        # Check if sector exists
        sector = fetchone_query('SELECT * FROM settori WHERE settore = %s', (settore,))
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
    def patch(self):
        # Gather parameters
        settore = request.args.get('settore')
        newValue = request.args.get('newValue')

        # Check if sector exists
        sector = fetchone_query('SELECT * FROM settori WHERE settore = %s', (settore,))
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
            query, params = 'SELECT settore FROM settori LIMIT %s OFFSET %s', (limit, offset)

            # Execute query
            sectors = fetchall_query(query, tuple(params))

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

api.add_resource(Sector, '/sector')
