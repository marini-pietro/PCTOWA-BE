from os.path import basename as os_path_basename
from flask import Blueprint, request, Response
from flask_restful import Api, Resource
from flask_jwt_extended import get_jwt_identity
from typing import List
from re import match as re_match
from config import (API_SERVER_HOST, API_SERVER_PORT, 
                    API_SERVER_NAME_IN_LOG, STATUS_CODES)
from .blueprints_utils import (check_authorization, build_select_query_from_filters, 
                               fetchone_query, fetchall_query, 
                               execute_query, log, jwt_required_endpoint, 
                               create_response, build_update_query_from_filters)

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
        sigla = request.json.get('sigla'),
        anno = request.json.get('anno')
        emailResponsabile = request.json.get('emailResponsabile')

        # Validate parameters
        missing_fields = [key for key, value in {"sigla": sigla, "anno": anno, "emailResponsabile": emailResponsabile}.items() if value is None]
        if missing_fields:
            return create_response(message={'error': f'missing required fields: {", ".join(missing_fields)}, check documentation'}, status_code=STATUS_CODES["bad_request"])
        if len(anno) != 5: 
            return create_response(message={'error': 'anno must be long 5 characters (e.g. 24-25)'}, status_code=STATUS_CODES["bad_request"])
        if not re_match(r'^\d{4}-\d{4}$', anno): # Check if the year string is in the format 'xx-xx'
            return create_response(message={'outcome': 'invalid anno format'}, status_code=STATUS_CODES["bad_request"])
        if not re_match(r'^([4-5]\d{0,1}[a-zA-Z]{2})$', sigla): # Check if the class variable is a number between 4 and 5 followed by two characters
            return create_response(message={'outcome': 'invalid sigla format'}, status_code=STATUS_CODES["bad_request"])
        if not re_match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', emailResponsabile): # Check if the email string is a valid email format
            return create_response(message={'outcome': 'invalid email format'}, status_code=STATUS_CODES["bad_request"])
            
        # Execute query to insert the class
        lastrowid: int = execute_query('INSERT INTO classi (sigla, anno, emailResponsabile) VALUES (%s, %s, %s)', (sigla, anno, emailResponsabile))

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
        
        # Check that the request has a JSON body
        if not request.is_json or request.json is None:
            return create_response(message={'error': 'Request body must be valid JSON with Content-Type: application/json'}, status_code=STATUS_CODES["bad_request"])

        # Check that class exists
        class_ = fetchone_query('SELECT * FROM classi WHERE idClasse = %s', (id,))
        if class_ is None:
            return create_response(message={'outcome': 'error, specified class does not exist'}, status_code=STATUS_CODES["not_found"])

        # Check that the specified fields actually exist in the database
        modifiable_columns: List[str] = ['sigla', 'emailResponsabile', 'anno']
        toModify: list[str]  = list(request.json.keys())
        error_columns = [field for field in toModify if field not in modifiable_columns]
        if error_columns:
            return create_response(message={'outcome': f'error, field(s) {error_columns} do not exist or cannot be modified'}, status_code=STATUS_CODES["bad_request"])

        # Build the update query
        query, params = build_update_query_from_filters(data=request.json, table_name='classi', 
                                                        id_column='idClasse', id_value=id)

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
    def get(self, emailResponsabile) -> Response:
        """
        Execute fuzzy search for class names in database.
        """

        # Log the read
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} requested to read class with email {emailResponsabile}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT
            )
        
        # Check if user exists
        user = fetchone_query(
            "SELECT * FROM utenti WHERE emailUtente = %s", (emailResponsabile)
        )
        if not user:
            return create_response(
                message={"outcome": "no user found with provided email"},
                status_code=STATUS_CODES["not_found"]
            )
        
        # Get class data
        classes_data = fetchall_query(
            "SELECT sigla, emailResponsabile, anno FROM classi WHERE emailResponsabile = %s", (emailResponsabile)
        )
        
        # Return the data
        return create_response(
            message=classes_data,
            status_code=STATUS_CODES["ok"]
        )

class ClassFuzzySearch(Resource):
    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor', 'teacher'])
    def get(self) -> Response:
        """
        Execute fuzzy search for class names in database.
        """

        # Gather parameters
        input_str = request.args.get('fnome')

        # Log the operation
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} requested fuzzy search in classes with string {input_str}', 
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT
            )

        # Get the data
        data = fetchall_query(
            "SELECT sigla "
            "FROM classi "
            "WHERE sigla LIKE %s",
            (f"%{input_str}%",)
        )

        # Return the data
        return create_response(
            message=data,
            status_code=STATUS_CODES["ok"]
        )

class ClassList(Resource):
    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor', 'teacher'])
    def get() -> Response:
        """
        Get the names of all classes.
        """

        # Log the read operation
        log(type='info', 
            message=f'User {get_jwt_identity().get("email")} read class list',
            origin_name=API_SERVER_NAME_IN_LOG, 
            origin_host=API_SERVER_HOST, 
            origin_port=API_SERVER_PORT
            )

        # Get data
        class_names = fetchall_query(
            "SELECT sigla FROM classi",
            ()
        )

        return create_response(
            message=class_names,
            status_code=STATUS_CODES["ok"]
        )

api.add_resource(Class, f'/{BP_NAME}', f'/{BP_NAME}/<int:id>', f'/{BP_NAME}/<str:email>')
api.add_resource(ClassList, f'/{BP_NAME}/list')
api.add_resource(ClassFuzzySearch, f'/{BP_NAME}/fsearch')