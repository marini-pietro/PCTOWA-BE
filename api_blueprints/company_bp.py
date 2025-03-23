from flask import Blueprint, jsonify, request
from flask_restful import Api, Resource
import mysql.connector
from utils import fetchone_query, execute_query, log, jwt_required_endpoint, parse_date_string

# Create the blueprint and API
company_bp = Blueprint('company', __name__)
api = Api(company_bp)

class CompanyRegister(Resource):
    @jwt_required_endpoint()
    def post(self):
        # Gather parameters
        ragioneSociale = request.args.get('ragioneSociale')
        nome = request.args.get('nome')
        sitoWeb = request.args.get('sitoWeb')
        indirizzoLogo = request.args.get('indirizzoLogo')
        codiceAteco = request.args.get('codiceAteco')
        partitaIVA = request.args.get('partitaIVA')
        telefonoAzienda = request.args.get('telefonoAzienda')
        fax = request.args.get('fax')
        emailAzienda = request.args.get('emailAzienda')
        pec = request.args.get('pec')
        formaGiuridica = request.args.get('formaGiuridica')
        dataConvenzione = request.args.get('dataConvenzione')
        scadenzaConvenzione = request.args.get('scadenzaConvenzione')
        settore = request.args.get('settore')
        categoria = request.args.get('categoria')

        # Insert the company
        try:
            execute_query(
                'INSERT INTO aziende (ragioneSociale, nome, sitoWeb, indirizzoLogo, codiceAteco, partitaIVA, telefonoAzienda, fax, emailAzienda, pec, formaGiuridica, dataConvenzione, scadenzaConvenzione, settore, categoria) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                (ragioneSociale, nome, sitoWeb, indirizzoLogo, codiceAteco, partitaIVA, telefonoAzienda, fax, emailAzienda, pec, formaGiuridica, dataConvenzione, scadenzaConvenzione, settore, categoria)
            )

            # Log the company creation
            log('info', f'User {request.user_identity} created a company')

            return jsonify({'outcome': 'company successfully created'}), 201
        except mysql.connector.IntegrityError as ex:
            return jsonify({'outcome': f'error, company already exists, integrity error: {ex}'}), 400

class CompanyDelete(Resource):
    @jwt_required_endpoint()
    def delete(self):
        # Gather parameters
        idAzienda = int(request.args.get('idAzienda'))

        # Check if company exists
        company = fetchone_query('SELECT * FROM aziende WHERE idAzienda = %s', (idAzienda,))
        if company is None:
            return jsonify({'outcome': 'error, specified company does not exist'})

        # Delete the company
        execute_query('DELETE FROM aziende WHERE idAzienda = %s', (idAzienda,))

        # Log the deletion
        log('info', f'User {request.user_identity} deleted company with id {idAzienda}')

        return jsonify({'outcome': 'company successfully deleted'})

class CompanyUpdate(Resource):
    @jwt_required_endpoint()
    def patch(self):
        # Gather parameters
        idAzienda = int(request.args.get('idAzienda'))
        toModify = request.args.get('toModify')
        newValue = request.args.get('newValue')

        # Check if the field to modify is allowed
        if toModify in ['idAzienda']:
            return jsonify({'outcome': 'error, specified field cannot be modified'})

        # Check if any casting operations are needed
        if toModify in ['telefonoAzienda', 'fax']:
            newValue = int(newValue)
        elif toModify in ['dataConvenzione', 'scadenzaConvenzione']:
            newValue = parse_date_string(date_string=newValue)

        # Check if company exists
        company = fetchone_query('SELECT * FROM aziende WHERE idAzienda = %s', (idAzienda,))
        if company is None:
            return jsonify({'outcome': 'error, specified company does not exist'})

        # Update the company
        execute_query(f'UPDATE aziende SET {toModify} = %s WHERE idAzienda = %s', (newValue, idAzienda))

        # Log the update
        log('info', f'User {request.user_identity} updated company with id {idAzienda}')

        return jsonify({'outcome': 'company successfully updated'})

class CompanyRead(Resource):
    @jwt_required_endpoint()
    def get(self):
        # Gather parameters
        try:
            idAzienda = int(request.args.get('idAzienda'))
        except (ValueError, TypeError):
            return jsonify({'error': 'invalid idAzienda parameter'}), 400

        # Execute query
        try:
            company = fetchone_query('SELECT * FROM aziende WHERE idAzienda = %s', (idAzienda,))

            # Log the read
            log('info', f'User {request.user_identity} read company with id {idAzienda}')

            return jsonify(company), 200
        except mysql.connector.Error as err:
            return jsonify({'error': str(err)}), 500

class CompanyBindTurn(Resource):
    @jwt_required_endpoint()
    def post(self):
        # Gather parameters
        idAzienda = int(request.args.get('idAzienda'))
        idTurno = int(request.args.get('idTurno'))

        # Check if company exists
        company = fetchone_query('SELECT * FROM aziende WHERE idAzienda = %s', (idAzienda,))
        if company is None:
            return {'outcome': 'error, specified company does not exist'}
        
        # Check if turn exists
        turn = fetchone_query('SELECT * FROM turni WHERE idTurno = %s', (idTurno,))
        if turn is None:
            return {'outcome': 'error, specified turn does not exist'}

        # Bind the company to the turn
        execute_query('INSERT INTO aziendaTurno (idAzienda, idTurno) VALUES (%s, %s)', (idAzienda, idTurno))

        # Log the binding
        log('info', f'User {request.user_identity} binded company with id {idAzienda} to turn with id {idTurno}')

        return {'outcome': 'success, company binded to turn successfully'}
    
class CompanyBindUser(Resource):
    @jwt_required_endpoint()
    def post(self):
        # Gather parameters
        idAzienda = int(request.args.get('idAzienda'))
        email = request.args.get('email')
        anno = request.args.get('anno')

        # Check if company exists
        company = fetchone_query('SELECT * FROM aziende WHERE idAzienda = %s', (idAzienda,))
        if company is None:
            return jsonify({'outcome': 'error, specified company does not exist'})
        
        # Check if user exists
        user = fetchone_query('SELECT * FROM utenti WHERE emailUtente = %s', (email,))
        if user is None:
            return jsonify({'outcome': 'error, specified user does not exist'})

        # Bind the company to the user
        execute_query('INSERT INTO aziendaUtente (idAzienda, emailUtente, anno) VALUES (%s, %s, %s)', (idAzienda, email, anno))

        # Log the binding
        log('info', f'User {request.user_identity} binded company with id {idAzienda} to user with email {email}')

        return jsonify({'outcome': 'success, company binded to user successfully'})

# Add resources to the API
api.add_resource(CompanyRegister, '/register')
api.add_resource(CompanyDelete, '/delete')
api.add_resource(CompanyUpdate, '/update')
api.add_resource(CompanyRead, '/read')