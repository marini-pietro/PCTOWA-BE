from flask import Blueprint, request, make_response, jsonify
from flask_restful import Api, Resource
import mysql.connector
from config import API_SERVER_HOST, API_SERVER_PORT, API_SERVER_NAME_IN_LOG
from .blueprints_utils import validate_filters, validate_inputs, build_query_from_filters, fetchone_query, fetchall_query, execute_query, log, jwt_required_endpoint

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
            
            return make_response(jsonify({'outcome': 'Class created'}), 201)
        except mysql.connector.IntegrityError:
            return make_response(jsonify({'outcome': 'Class already exists'}), 400)

class ClassDelete(Resource):
    @jwt_required_endpoint
    def delete(self):
        class_id = request.args.get('idClasse')
        if not fetchone_query('SELECT * FROM classi WHERE idClasse = %s', (class_id,)):
            return make_response(jsonify({'outcome': 'Class not found'}), 404)
            
        
        execute_query('DELETE FROM classi WHERE idClasse = %s', (class_id,))
        
        log(type='info', message=f'User {request.user_identity} deleted class',
            origin_name=API_SERVER_NAME_IN_LOG, origin_host=API_SERVER_HOST, origin_port=API_SERVER_PORT)
        
        return make_response(jsonify({'outcome': 'Class deleted'}), 200)

class ClassUpdate(Resource):
    allowed_fields = ['classe', 'anno', 'emailResponsabile']
    
    @jwt_required_endpoint
    def patch(self):
        class_id = request.args.get('idClasse')
        field = request.args.get('toModify')
        value = request.args.get('newValue')

        if field not in self.allowed_fields:
            return make_response(jsonify({'outcome': 'Invalid field'}), 400)

        if not fetchone_query('SELECT * FROM classi WHERE idClasse = %s', (class_id,)):
            return {'outcome': 'Class not found'}, 404

        execute_query(f'UPDATE classi SET {field} = %s WHERE idClasse = %s', (value, class_id))
        
        log(type='info', message=f'User {request.user_identity} updated class',
            origin_name=API_SERVER_NAME_IN_LOG, origin_host=API_SERVER_HOST, origin_port=API_SERVER_PORT)
        
        return make_response(jsonify({'outcome': 'class updated'}), 200)

class ClassRead(Resource):
    @jwt_required_endpoint
    def get(self):
        try:
            limit = int(request.args.get('limit', 10))
            offset = int(request.args.get('offset', 0))
        except ValueError:
            return make_response(jsonify({'error': 'Invalid pagination'}), 400)

        data = request.get_json()
        if (validation := validate_filters(data, 'classi')) is not True:
            return validation, 400

        try:
            query, params = build_query_from_filters(
                data=data, table_name='classi',
                limit=limit, offset=offset
            )
            classes = [dict(row) for row in fetchall_query(query, tuple(params))]
            return classes, 200
        except Exception as err:
            return make_response(jsonify({'error': str(err)}), 500)

api.add_resource(ClassRegister, '/register')
api.add_resource(ClassDelete, '/delete')
api.add_resource(ClassUpdate, '/update')
api.add_resource(ClassRead, '/read')