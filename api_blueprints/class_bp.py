from flask import Blueprint, jsonify, request
from flask_restful import Api, Resource
import mysql.connector
from utils import fetchone_query, execute_query, log, jwt_required_endpoint

# Create the blueprint and API
classes_bp = Blueprint('classes', __name__)
api = Api(classes_bp)

class ClassRegister(Resource):
    @jwt_required_endpoint()
    def post(self):
        # Gather parameters
        classe = request.args.get('classe')
        anno = request.args.get('anno')
        emailResponsabile = request.args.get('emailResponsabile')

        try:
            execute_query('INSERT INTO classi VALUES (%s, %s, %s)', (classe, anno, emailResponsabile))

            # Log the class creation
            log('info', f'User {request.user_identity} created class {classe}')

            return jsonify({"outcome": "class successfully created"}), 201
        except mysql.connector.IntegrityError:
            return jsonify({'outcome': 'error, class with provided credentials already exists'}), 400

class ClassDelete(Resource):
    @jwt_required_endpoint()
    def delete(self):
        # Gather parameters
        idClasse = request.args.get('idClasse')

        # Check if class exists
        classe = fetchone_query('SELECT * FROM classi WHERE idClasse = %s', (idClasse,))
        if classe is None:
            return jsonify({'outcome': 'error, specified class does not exist'})

        # Delete the class
        execute_query('DELETE FROM classi WHERE idClasse = %s', (idClasse,))

        # Log the deletion
        log('info', f'User {request.user_identity} deleted class')

        return jsonify({'outcome': 'class successfully deleted'})

class ClassUpdate(Resource):
    @jwt_required_endpoint()
    def patch(self):
        # Gather parameters
        idClasse = request.args.get('idClasse')
        toModify = request.args.get('toModify')
        newValue = request.args.get('newValue')

        # Check if the field to modify is allowed
        if toModify in ['idClasse']:
            return jsonify({'outcome': 'error, specified field cannot be modified'})

        # Check if class exists
        classe = fetchone_query('SELECT * FROM classi WHERE idClasse = %s', (idClasse,))
        if classe is None:
            return jsonify({'outcome': 'error, specified class does not exist'})

        # Update the class
        execute_query(f'UPDATE classi SET {toModify} = %s WHERE idClasse = %s', (newValue, idClasse))

        # Log the update
        log('info', f'User {request.user_identity} updated class')

        return jsonify({'outcome': 'class successfully updated'})

class ClassRead(Resource):
    @jwt_required_endpoint()
    def get(self):
        # Gather parameters
        try:
            idClasse = int(request.args.get('idClasse'))
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid idClasse parameter"}), 400

        # Execute query
        try:
            class_ = fetchone_query('SELECT * FROM classi WHERE idClasse = %s', (idClasse,))

            # Log the read
            log('info', f'User {request.user_identity} read class')

            return jsonify(class_), 200
        except mysql.connector.Error as err:
            return jsonify({"error": str(err)}), 500

# Add resources to the API
api.add_resource(ClassRegister, '/register')
api.add_resource(ClassDelete, '/delete')
api.add_resource(ClassUpdate, '/update')
api.add_resource(ClassRead, '/read')