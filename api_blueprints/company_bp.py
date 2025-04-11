from os.path import basename as os_path_basename
from flask import Blueprint, request, Response
from flask_restful import Api, Resource
from flask_jwt_extended import get_jwt_identity
from re import match as re_match
from typing import List
from config import (API_SERVER_HOST, API_SERVER_PORT, 
                    API_SERVER_NAME_IN_LOG, STATUS_CODES)
from .blueprints_utils import (check_authorization, build_select_query_from_filters, 
                               fetchone_query, fetchall_query, 
                               execute_query, log, 
                               jwt_required_endpoint, create_response, 
                               build_update_query_from_filters, parse_date_string)

# Define constants
BP_NAME = os_path_basename(__file__).replace('_bp.py', '')

# Create the blueprint and API
company_bp = Blueprint(BP_NAME, __name__)
api = Api(company_bp)

class Company(Resource):
    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor'])
    def post(self) -> Response:
        """
        Create a new company in the database.
        The request body must be a JSON object with application/json content type.
        """
        
        # Ensure the request has a JSON body
        if not request.is_json or request.json is None:
            return create_response(message={'error': 'Request body must be valid JSON with Content-Type: application/json'}, status_code=STATUS_CODES["bad_request"])

        # Gather parameters from the request body (new dictionary is necessary so that user can provide JSON with fields in any order)
        params = {
            'ragioneSociale': request.json.get('ragioneSociale'),
            'nome': request.json.get('nome'),
            'sitoWeb': request.json.get('sitoWeb'),
            'indirizzoLogo': request.json.get('indirizzoLogo'),
            'codiceAteco': request.json.get('codiceAteco'),
            'partitaIVA': request.json.get('partitaIVA'),
            'telefonoAzienda': request.json.get('telefonoAzienda'),
            'fax': request.json.get('fax'),
            'emailAzienda': request.json.get('emailAzienda'),
            'pec': request.json.get('pec'),
            'formaGiuridica': request.json.get('formaGiuridica'),
            'dataConvenzione': parse_date_string(request.json.get('dataConvenzione')),
            'scadenzaConvenzione': parse_date_string(request.json.get('scadenzaConvenzione')),
            'settore': request.json.get('settore'),
            'categoria': request.json.get('categoria')
        }

        # Validate parameters
        if not re_match(r'^\+\d{1,3}\s?\d{4,14}$', params['telefonoAzienda']):
            return create_response(message={'error': 'invalid phone number format'}, status_code=STATUS_CODES["bad_request"])
        # TODO: add regex check to all the other fields
        
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
            message=f'User {get_jwt_identity().get("email")} created company {lastrowid}',
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            origin_port=API_SERVER_PORT
        )

        # Return a success message
        return create_response(message={'outcome': 'company successfully created',
                                        'location': f'http://{API_SERVER_HOST}:{API_SERVER_PORT}/api/{BP_NAME}/{lastrowid}'}, status_code=STATUS_CODES["created"])
        
    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor'])
    def delete(self, id) -> Response:
        """
        Delete a company from the database.
        The company ID is passed as a path variable.
        """
        # Check if specified company exists
        company = fetchone_query('SELECT * FROM aziende WHERE idAzienda = %s', (id,))
        if not company:
            return create_response(message={'outcome': 'error, company does not exist'}, status_code=STATUS_CODES["not_found"])

        # Delete the company
        execute_query('DELETE FROM aziende WHERE idAzienda = %s', (id,))
        
        # Log the deletion of the company
        log(
            type='info',
            message=f'User {get_jwt_identity().get("email")} deleted company {id}',
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            origin_port=API_SERVER_PORT
        )

        # Return a success message
        return create_response(message={'outcome': 'company successfully deleted'}, status_code=STATUS_CODES["no_content"])

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor'])
    def patch(self, id) -> Response:
        """
        Update a company in the database.
        The company ID is passed as a path variable.
        """

        # Check that the request has a JSON body
        if not request.is_json or request.json is None:
            return create_response(message={'error': 'Request body must be valid JSON with Content-Type: application/json'}, status_code=STATUS_CODES["bad_request"])

        # Check if the company exists
        company = fetchone_query('SELECT * FROM aziende WHERE idAzienda = %s', (id,))
        if not company:
            return create_response(message={'outcome': 'error, company does not exist'}, status_code=STATUS_CODES["not_found"])

        # Check that the specified fields can be modified
        not_allowed_fields = ['idAzienda']
        for field in toModify:
            if field in not_allowed_fields:
                return create_response(message={'outcome': f'error, field "{field}" cannot be modified'}, status_code=STATUS_CODES["bad_request"])

        # Check that the specified fields actually exist in the database
        modifiable_columns: List[str] = ['ragioneSociale', 'codiceAteco', 
                              'partitaIVA', 'fax', 
                              'pec', 'telefonoAzienda',
                              'emailAzienda', 'dataConvenzione', 
                              'scadenzaConvenzione', 'categoria', 
                              'indirizzoLogo', 'sitoWeb', 
                              'formaGiuridica']
        toModify: list[str]  = list(request.json.keys())
        error_columns = [field for field in toModify if field not in modifiable_columns]
        if error_columns:
            return create_response(message={'outcome': f'error, field(s) {error_columns} do not exist or cannot be modified'}, status_code=STATUS_CODES["bad_request"])

        # Build the update query
        query, params = build_update_query_from_filters(
            data=request.json, table_name='aziende', 
            id_column='idAzienda', id_value=id
        )

        # Execute the update query
        execute_query(query, params)

        # Log the update of the company        
        log(
            type='info',
            message=f'User {get_jwt_identity().get("email")} updated company {id}',
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            origin_port=API_SERVER_PORT
        )

        # Return a success message
        return create_response(message={'outcome': 'company successfully updated'}, status_code=STATUS_CODES["ok"])

    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor', 'teacher'])
    def get(self, id) -> Response:
        """
        Retrieve a company from the database.
        The company ID is passed as a path variable.
        """
        # Gather parameters
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
            return create_response(message={'error': 'invalid limit or offset values'}, status_code=STATUS_CODES["bad_request"])
        
        # Build the filters dictionary (only include non-null values)
        data = {key: value for key, value in {
            'idAzienda': id,  # Use the path variable 'id'
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
                message=f'User {get_jwt_identity().get("email")} read companies {ids}',
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                origin_port=API_SERVER_PORT
            )

            # Return the companies
            return create_response(message=companies, status_code=STATUS_CODES["ok"])
        except Exception as err:
            return create_response(message={'error': str(err)}, status_code=STATUS_CODES["internal_error"])

api.add_resource(Company, f'/{BP_NAME}', f'/{BP_NAME}/<int:id>')