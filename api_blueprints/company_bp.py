from flask import Blueprint, request
from flask_restful import Api, Resource
import mysql.connector
from config import API_SERVER_HOST, API_SERVER_PORT, API_SERVER_NAME_IN_LOG
from .blueprints_utils import (
    validate_filters, build_query_from_filters, 
    fetchone_query, fetchall_query, execute_query, 
    log, jwt_required_endpoint, parse_date_string
)

# Create the blueprint and API
company_bp = Blueprint('company', __name__)
api = Api(company_bp)

class CompanyRegister(Resource):
    @jwt_required_endpoint
    def post(self):
        params = {
            'ragioneSociale': request.args.get('ragioneSociale'),
            'nome': request.args.get('nome'),
            'sitoWeb': request.args.get('sitoWeb'),
            'indirizzoLogo': request.args.get('indirizzoLogo'),
            'codiceAteco': request.args.get('codiceAteco'),
            'partitaIVA': request.args.get('partitaIVA'),
            'telefonoAzienda': request.args.get('telefonoAzienda'),
            'fax': request.args.get('fax'),
            'emailAzienda': request.args.get('emailAzienda'),
            'pec': request.args.get('pec'),
            'formaGiuridica': request.args.get('formaGiuridica'),
            'dataConvenzione': request.args.get('dataConvenzione'),
            'scadenzaConvenzione': request.args.get('scadenzaConvenzione'),
            'settore': request.args.get('settore'),
            'categoria': request.args.get('categoria')
        }

        try:
            execute_query(
                '''INSERT INTO aziende 
                (ragioneSociale, nome, sitoWeb, indirizzoLogo, codiceAteco, 
                 partitaIVA, telefonoAzienda, fax, emailAzienda, pec, 
                 formaGiuridica, dataConvenzione, scadenzaConvenzione, settore, categoria) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                tuple(params.values())
            )

            log(
                type='info',
                message=f'User {request.user_identity} created a company',
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                origin_port=API_SERVER_PORT
            )

            return {'outcome': 'company successfully created'}, 201
        except mysql.connector.IntegrityError as ex:
            return {'outcome': f'error, company already exists: {ex}'}, 400

class CompanyDelete(Resource):
    @jwt_required_endpoint
    def delete(self):
        idAzienda = int(request.args.get('idAzienda'))
        company = fetchone_query('SELECT * FROM aziende WHERE idAzienda = %s', (idAzienda,))
        
        if not company:
            return {'outcome': 'error, company does not exist'}, 404

        execute_query('DELETE FROM aziende WHERE idAzienda = %s', (idAzienda,))
        
        log(
            type='info',
            message=f'User {request.user_identity} deleted company {idAzienda}',
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            origin_port=API_SERVER_PORT
        )

        return {'outcome': 'company successfully deleted'}

class CompanyUpdate(Resource):
    @jwt_required_endpoint
    def patch(self):
        idAzienda = int(request.args.get('idAzienda'))
        to_modify = request.args.get('toModify')
        new_value = request.args.get('newValue')

        if to_modify in ['idAzienda']:
            return {'outcome': 'error, invalid field to modify'}, 400

        if to_modify in ['telefonoAzienda', 'fax']:
            new_value = int(new_value)
        elif to_modify in ['dataConvenzione', 'scadenzaConvenzione']:
            new_value = parse_date_string(new_value)

        company = fetchone_query('SELECT * FROM aziende WHERE idAzienda = %s', (idAzienda,))
        if not company:
            return {'outcome': 'error, company does not exist'}, 404

        execute_query(f'UPDATE aziende SET {to_modify} = %s WHERE idAzienda = %s', (new_value, idAzienda))
        
        log(
            type='info',
            message=f'User {request.user_identity} updated company {idAzienda}',
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            origin_port=API_SERVER_PORT
        )

        return {'outcome': 'company successfully updated'}

class CompanyRead(Resource):
    @jwt_required_endpoint
    def get(self):
        try:
            limit = int(request.args.get('limit', 10))
            offset = int(request.args.get('offset', 0))
        except ValueError:
            return {'error': 'invalid limit/offset format'}, 400

        data = request.get_json()
        validation = validate_filters(data=data, table_name='aziende')
        
        if validation is not True:
            return validation, 400

        try:
            query, params = build_query_from_filters(
                data=data,
                table_name='aziende',
                limit=limit,
                offset=offset
            )
            
            companies = fetchall_query(query, tuple(params))
            
            if not companies:
                return {'outcome': 'no companies found'}, 404

            # Convert rows to dictionaries
            companies = [dict(row) for row in companies]
            
            log(
                type='info',
                message=f'User {request.user_identity} read companies',
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                origin_port=API_SERVER_PORT
            )

            return companies, 200
        except Exception as err:
            return {'error': str(err)}, 500

class CompanyBindTurn(Resource):
    @jwt_required_endpoint
    def post(self):
        idAzienda = int(request.args.get('idAzienda'))
        idTurno = int(request.args.get('idTurno'))

        if not fetchone_query('SELECT * FROM aziende WHERE idAzienda = %s', (idAzienda,)):
            return {'outcome': 'error, company not found'}, 404

        if not fetchone_query('SELECT * FROM turni WHERE idTurno = %s', (idTurno,)):
            return {'outcome': 'error, turn not found'}, 404

        execute_query('INSERT INTO aziendaTurno (idAzienda, idTurno) VALUES (%s, %s)', (idAzienda, idTurno))
        
        log(
            type='info',
            message=f'User {request.user_identity} bound company {idAzienda} to turn {idTurno}',
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            origin_port=API_SERVER_PORT
        )

        return {'outcome': 'company-turn binding successful'}

class CompanyBindUser(Resource):
    @jwt_required_endpoint
    def post(self):
        idAzienda = int(request.args.get('idAzienda'))
        email = request.args.get('email')
        anno = request.args.get('anno')

        if not fetchone_query('SELECT * FROM aziende WHERE idAzienda = %s', (idAzienda,)):
            return {'outcome': 'error, company not found'}, 404

        if not fetchone_query('SELECT * FROM utenti WHERE emailUtente = %s', (email,)):
            return {'outcome': 'error, user not found'}, 404

        execute_query('INSERT INTO aziendaUtente (idAzienda, emailUtente, anno) VALUES (%s, %s, %s)', (idAzienda, email, anno))
        
        log(
            type='info',
            message=f'User {request.user_identity} bound company {idAzienda} to user {email}',
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            origin_port=API_SERVER_PORT
        )

        return {'outcome': 'company-user binding successful'}

# Add resources to the API
api.add_resource(CompanyRegister, '/register')
api.add_resource(CompanyDelete, '/delete')
api.add_resource(CompanyUpdate, '/update')
api.add_resource(CompanyRead, '/read')
api.add_resource(CompanyBindTurn, '/bind-turn')
api.add_resource(CompanyBindUser, '/bind-user')