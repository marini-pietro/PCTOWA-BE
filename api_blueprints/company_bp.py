from flask import Blueprint, request
from flask_restful import Api, Resource
import mysql.connector
from config import API_SERVER_HOST, API_SERVER_PORT, API_SERVER_NAME_IN_LOG, STATUS_CODES
from .blueprints_utils import (check_authorization, validate_filters, 
                               build_select_query_from_filters, fetchone_query, 
                               fetchall_query, execute_query, 
                               log, jwt_required_endpoint, 
                               create_response, validate_filters, 
                               build_update_query_from_filters)

# Create the blueprint and API
company_bp = Blueprint('company', __name__)
api = Api(company_bp)

class CompanyRegister(Resource):
    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor'])
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

        #TODO: add regex validation for each field

        try:
            lastrowid = execute_query(
                '''INSERT INTO aziende 
                (ragioneSociale, nome, sitoWeb, indirizzoLogo, codiceAteco, 
                 partitaIVA, telefonoAzienda, fax, emailAzienda, pec, 
                 formaGiuridica, dataConvenzione, scadenzaConvenzione, settore, categoria) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                tuple(params.values())
            )

            # Log the creation of the company
            log(
                type='info',
                message=f'User {request.user_identity} created company {lastrowid}',
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                origin_port=API_SERVER_PORT
            )

            # Return a success message
            return create_response(message={'outcome': 'company successfully created'}, status_code=STATUS_CODES["created"])
        except mysql.connector.IntegrityError as ex:
            return create_response(message={'outcome': f'error, company already exists: {ex}'}, status_code=STATUS_CODES["bad_request"])

class CompanyDelete(Resource):
    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor'])
    def delete(self):
        # Gather parameters
        try:
            idAzienda = int(request.args.get('idAzienda'))
        except (ValueError, TypeError):
            return create_response(message={'outcome': 'invalid company ID'}, status_code=STATUS_CODES["bad_request"])
        
        # Check if specified company exists
        company = fetchone_query('SELECT * FROM aziende WHERE idAzienda = %s', (idAzienda,))
        if not company:
            return create_response(message={'outcome': 'error, company does not exist'}, status_code=STATUS_CODES["not_found"])

        # Delete the company
        execute_query('DELETE FROM aziende WHERE idAzienda = %s', (idAzienda,))
        
        # Log the deletion of the company
        log(
            type='info',
            message=f'User {request.user_identity} deleted company {idAzienda}',
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            origin_port=API_SERVER_PORT
        )

        # Return a success message
        return create_response(message={'outcome': 'company successfully deleted'}, status_code=STATUS_CODES["no_content"])

class CompanyUpdate(Resource):
    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor'])
    def patch(self):
        # Gather parameters
        toModify: list[str] = request.args.get('toModify').split(',')  # list of fields to modify
        newValues: list[str] = request.args.get('newValue').split(',')  # list of values to set
        try:
            idAzienda = int(request.args.get('idAzienda'))
        except (ValueError, TypeError):
            return create_response(message={'outcome': 'invalid company ID'}, status_code=STATUS_CODES["bad_request"])

        # Validate parameters
        if len(toModify) != len(newValues):
            return create_response(message={'outcome': 'Mismatched fields and values lists lengths'}, status_code=STATUS_CODES["bad_request"])

        # Build a dictionary with fields as keys and values as values
        updates = dict(zip(toModify, newValues))  # {field1: value1, field2: value2, ...}

        # Check that the specified fields can be modified
        not_allowed_fields = ['idAzienda']
        for field in toModify:
            if field in not_allowed_fields:
                return create_response(message={'outcome': f'error, field "{field}" cannot be modified'}, status_code=STATUS_CODES["bad_request"])

        # Check that the specified fields actually exist in the database
        outcome = validate_filters(data=updates, table_name='aziende')
        if outcome is not True:
            return outcome, STATUS_CODES["bad_request"]

        # Check if the company exists
        company = fetchone_query('SELECT * FROM aziende WHERE idAzienda = %s', (idAzienda,))
        if not company:
            return create_response(message={'outcome': 'error, company does not exist'}, status_code=STATUS_CODES["not_found"])

        # Log the update of the company        
        log(
            type='info',
            message=f'User {request.user_identity} updated company {idAzienda}',
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            origin_port=API_SERVER_PORT
        )

        # Build the update query
        query, params = build_update_query_from_filters(
            data=updates, table_name='aziende', id=idAzienda
        )

        # Execute the update query
        execute_query(query, params)

        # Return a success message
        return create_response(message={'outcome': 'company successfully updated'}, status_code=STATUS_CODES["ok"])

class CompanyRead(Resource):
    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor', 'teacher'])
    def get(self):
        # Gather parameters
        idAzienda = request.args.get('idAzienda')
        ragioneSociale = request.args.get('ragioneSociale')
        codiceAteco = request.args.get('codiceAteco')
        partitaIVA = request.args.get('partitaIVA')
        fax = request.args.get('fax')
        pec = request.args.get('pec')
        telefonoAzienda = request.args.get('telefonoAzienda')
        emailAzienda = request.args.get('emailAzienda')
        dataConvenzione = request.args.get('dataConvenzione')
        scadenzaConvenzione = request.args.get('scadenzaConvenzione')
        categoria = request.args.get('categoria')
        indirizzoLogo = request.args.get('indirizzoLogo')
        sitoWeb = request.args.get('sitoWeb')
        formaGiuridica = request.args.get('formaGiuridica')
        try:
            limit = int(request.args.get('limit', 10))
            offset = int(request.args.get('offset', 0))
        except ValueError:
            return {'error': 'invalid limit or offset values'}, STATUS_CODES["bad_request"]
        
        # Build the filters dictionary (only include non-null values)
        data = {key: value for key, value in {
            'idAzienda': idAzienda,
            'ragioneSociale': ragioneSociale,
            'codiceAteco': codiceAteco,
            'partitaIVA': partitaIVA,
            'fax': fax,
            'pec': pec,
            'telefonoAzienda': telefonoAzienda,
            'emailAzienda': emailAzienda,
            'dataConvenzione': dataConvenzione,
            'scadenzaConvenzione': scadenzaConvenzione,
            'categoria': categoria,
            'indirizzoLogo': indirizzoLogo,
            'sitoWeb': sitoWeb,
            'formaGiuridica': formaGiuridica
        }.items() if value}

        try:
            # Build the select query
            query, params = build_select_query_from_filters(
                data=data,
                table_name='aziende',
                limit=limit,
                offset=offset
            )
            
            # Execute the query
            companies = fetchall_query(query, params)

            # Get the ids to log
            ids = [company['idAzienda'] for company in companies]

            # Log the read operation            
            log(
                type='info',
                message=f'User {request.user_identity} read companies {ids}',
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                origin_port=API_SERVER_PORT
            )

            # Return the companies
            return companies, STATUS_CODES["ok"]
        except Exception as err:
            return create_response(message={'error': str(err)}, status_code=STATUS_CODES["internal_error"])

# Add resources to the API
api.add_resource(CompanyRegister, '/register')
api.add_resource(CompanyDelete, '/delete')
api.add_resource(CompanyUpdate, '/update')
api.add_resource(CompanyRead, '/read')