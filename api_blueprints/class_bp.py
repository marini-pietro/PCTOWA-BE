from flask import Blueprint, request
from flask_restful import Api, Resource
import mysql.connector
from config import API_SERVER_HOST, API_SERVER_PORT, API_SERVER_NAME_IN_LOG, STATUS_CODES
from .blueprints_utils import validate_filters, validate_inputs, build_query_from_filters, fetchone_query, fetchall_query, execute_query, log, jwt_required_endpoint, create_response

class_bp = Blueprint('class', __name__)
api = Api(class_bp)

class ClassRegister(Resource):
    @jwt_required_endpoint
    def post(self):
        try:
            class_data = {
                'classe': request.args.get('classe'),
                'anno': request.args.get('anno'),
                'emailResponsabile': request.args.get('emailResponsabile')
            }
            
            execute_query('INSERT INTO classi VALUES (%s, %s, %s)', tuple(class_data.values()))
            
            log(type='info', message=f'User {request.user_identity} created class',
                origin_name=API_SERVER_NAME_IN_LOG, origin_host=API_SERVER_HOST, origin_port=API_SERVER_PORT)
            
            return create_response(message={'outcome': 'Class created'}, status_code=STATUS_CODES["created"])
        except mysql.connector.IntegrityError:
            return create_response(message={'outcome': 'Class already exists'}, status_code=STATUS_CODES["bad_request"])

class ClassDelete(Resource):
    @jwt_required_endpoint
    def delete(self):
        class_id = request.args.get('idClasse')
        if not fetchone_query('SELECT * FROM classi WHERE idClasse = %s', (class_id,)):
            return create_response(message={'outcome': 'Class not found'}, status_code=STATUS_CODES["not_found"])
              
        execute_query('DELETE FROM classi WHERE idClasse = %s', (class_id,))
        
        log(type='info', message=f'User {request.user_identity} deleted class',
            origin_name=API_SERVER_NAME_IN_LOG, origin_host=API_SERVER_HOST, origin_port=API_SERVER_PORT)
        
        return create_response(message={'outcome': 'Class deleted'}, status_code=STATUS_CODES["ok"])

class ClassUpdate(Resource):
    allowed_fields = ['classe', 'anno', 'emailResponsabile']
    
    @jwt_required_endpoint
    def patch(self):
        class_id = request.args.get('idClasse')
        field = request.args.get('toModify')
        value = request.args.get('newValue')

        if field not in self.allowed_fields:
            return create_response(message={'outcome': 'Invalid field'}, status_code=STATUS_CODES["bad_request"])

        if not fetchone_query('SELECT * FROM classi WHERE idClasse = %s', (class_id,)):
            return {'outcome': 'Class not found'}, STATUS_CODES["not_found"]

        execute_query(f'UPDATE classi SET {field} = %s WHERE idClasse = %s', (value, class_id))
        
        log(type='info', message=f'User {request.user_identity} updated class',
            origin_name=API_SERVER_NAME_IN_LOG, origin_host=API_SERVER_HOST, origin_port=API_SERVER_PORT)
        
        return create_response(message={'outcome': 'class updated'}, status_code=STATUS_CODES["ok"])

class ClassRead(Resource):
    @jwt_required_endpoint
    def get(self):
        try:
            limit = int(request.args.get('limit', 10))
            offset = int(request.args.get('offset', 0))
        except ValueError:
            return create_response(message={'error': 'Invalid pagination'}, status_code=STATUS_CODES["bad_request"])

        data = request.get_json()
        if (validation := validate_filters(data, 'classi')) is not True:
            return validation, STATUS_CODES["bad_request"]

        try:
            query, params = build_query_from_filters(
                data=data, table_name='classi',
                limit=limit, offset=offset
            )
            classes = [dict(row) for row in fetchall_query(query, tuple(params))]
            return classes, STATUS_CODES["ok"]
        except Exception as err:
            return create_response(message={'error': str(err)}, status_code=STATUS_CODES["internal_error"])

api.add_resource(ClassRegister, '/register')
api.add_resource(ClassDelete, '/delete')
api.add_resource(ClassUpdate, '/update')
api.add_resource(ClassRead, '/read')