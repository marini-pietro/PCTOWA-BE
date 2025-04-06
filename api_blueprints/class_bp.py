from os.path import basename as os_path_basename
from flask import Blueprint, request, Response
from flask_restful import Api, Resource
from flask_jwt_extended import get_jwt_identity
from config import API_SERVER_HOST, API_SERVER_PORT, API_SERVER_NAME_IN_LOG, STATUS_CODES
from mysql.connector import IntegrityError
from re import match as re_match
from .blueprints_utils import (check_authorization, build_select_query_from_filters, 
                               fetchone_query, fetchall_query, 
                               execute_query, log, jwt_required_endpoint, 
                               create_response, validate_filters, 
                               build_update_query_from_filters)

# Define constants
BP_NAME = os_path_basename(__file__).replace('_bp.py', '')

# Create the blueprint and the API
class_bp = Blueprint(BP_NAME, __name__)
api = Api(class_bp)

class Class(Resource):
    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor'])
    def post(self) -> Response:
        """
        Create a new class in the database.
        The request body must be a JSON object with application/json content type.
        """

        # Ensure the request has a JSON body
        if not request.is_json or request.json is None:
            return create_response(message={'error': 'Request body must be valid JSON with Content-Type: application/json'}, status_code=STATUS_CODES["bad_request"])

        # Gather parameters
        classe = request.json.get('classe'),
        anno = request.json.get('anno')
        emailResponsabile = request.json.get('emailResponsabile')

        # Validate parameters
        if not re_match(r'^\d{4}-\d{4}$', anno):
            return create_response(message={'outcome': 'invalid anno format'}, status_code=STATUS_CODES["bad_request"])
        if not re_match(r'^[a-zA-Z0-9]+$', classe):
            return create_response(message={'outcome': 'invalid classe format'}, status_code=STATUS_CODES["bad_request"])
        if not re_match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', emailResponsabile):
            return create_response(message={'outcome': 'invalid email format'}, status_code=STATUS_CODES["bad_request"])
            
        # Execute query to insert the class
        lastrowid: int = execute_query('INSERT INTO classi (classe, anno, emailResponsabile) VALUES (%s, %s, %s)', (classe, anno, emailResponsabile))

        # Log the creation of the class
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} created class {lastrowid}',
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)
            
        # Return a success message
        return create_response(message={'outcome': 'class created',
                                            'location': f'http://{API_SERVER_HOST}:{API_SERVER_PORT}/api/{BP_NAME}/{lastrowid}'}, status_code=STATUS_CODES["created"])

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor'])
    def delete(self, id) -> Response:
        """
        Delete a class from the database.
        The class ID is passed as a path parameter.
        """
        # Delete the class
        execute_query('DELETE FROM classi WHERE idClasse = %s', (id,))
        
        # Log the deletion of the class
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} deleted class {id}',
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)
        
        # Return a success message
        return create_response(message={'outcome': 'class deleted'}, status_code=STATUS_CODES["no_content"])

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor'])
    def patch(self, id) -> Response:
        """
        Update a class in the database.
        The class ID is passed as a path parameter.
        """
        # Gather parameters
        toModify: list[str] = request.args.get('toModify').split(',')  # list of fields to modify
        newValues: list[str] = request.args.get('newValue').split(',')  # list of values to set

        # Validate parameters
        if len(toModify) != len(newValues):
            return create_response(message={'outcome': 'Mismatched fields and values lists lengths'}, status_code=STATUS_CODES["bad_request"])

        # Build a dictionary with fields as keys and values as values
        updates = dict(zip(toModify, newValues))  # {field1: value1, field2: value2, ...}

        # Check that the specified fields can be modified
        not_allowed_fields: list[str] = ['idClasse']
        for field in toModify:
            if field in not_allowed_fields:
                return create_response(message={'outcome': f'error, field "{field} cannot be modified"'}, status_code=STATUS_CODES["bad_request"])

        # Check that the specified fields actually exist in the database
        outcome = validate_filters(toModify, 'classi')
        if outcome is not True:
            return create_response(outcome, STATUS_CODES["bad_request"])

        # Check that the specified class exists
        class_ = fetchone_query('SELECT * FROM classi WHERE idClasse = %s', (id,))
        if not class_:
            return create_response({'outcome': 'specified class does not exist'}, STATUS_CODES["not_found"])

        # Build the update query
        query, params = build_update_query_from_filters(data=updates, table_name='classi', id=id)

        # Execute the update query
        execute_query(query, params)
        
        # Log the update of the class
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} updated class {id}',
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT)
        
        # Return a success message
        return create_response(message={'outcome': 'class updated'}, status_code=STATUS_CODES["ok"])
    
    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor', 'teacher'])
    def get(self, id) -> Response:
        """
        Get a class from the database.
        The class ID is passed as a path parameter.
        """
        # Gather parameters
        classe = request.args.get('classe')
        anno = request.args.get('anno')
        emailResponsabile = request.args.get('emailResponsabile')
        try:
            limit = int(request.args.get('limit', 10))  # Default limit to 10 if not provided
            offset = int(request.args.get('offset', 0))  # Default offset to 0 if not provided
        except (ValueError, TypeError):
            return create_response(message={'error': 'Invalid limit or offset values'}, status_code=STATUS_CODES["bad_request"])

        # Build the filters dictionary (only include non-null values)
        data = {key: value for key, value in {
            'idClasse': id,  # Use the path variable 'id'
            'classe': classe,
            'anno': anno,
            'emailResponsabile': emailResponsabile
        }.items() if value}

        try:
            # Build the select query
            query, params = build_select_query_from_filters(
                data=data, 
                table_name='classi',
                limit=limit, 
                offset=offset
            )

            # Execute the query
            classes = fetchall_query(query, params)

            # Get the ids to log
            ids = [class_['idClasse'] for class_ in classes]

            # Log the read operation
            log(type='info', 
                message=f'User {get_jwt_identity().get("email")} read classes {ids}',
                origin_name=API_SERVER_NAME_IN_LOG, 
                origin_host=API_SERVER_HOST, 
                origin_port=API_SERVER_PORT
            )

            # Return the results
            return create_response(message=classes, status_code=STATUS_CODES["ok"])
        except Exception as err:
            return create_response(message={'error': str(err)}, status_code=STATUS_CODES["internal_error"])

api.add_resource(Class, f'/{BP_NAME}', f'/{BP_NAME}/<int:id>')