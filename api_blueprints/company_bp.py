from os.path import basename as os_path_basename
from flask import Blueprint, request, Response
from flask_restful import Api, Resource
from flask_jwt_extended import get_jwt_identity
from re import match as re_match
from typing import List, Dict, Any
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

        try:
            
            # Execute the query
            company = fetchone_query("SELECT * FROM aziende WHERE = %s", (id, ))

            # Build turn ids endpoints list
            if company:
                turn_ids: List[Dict[str, Any]] = fetchall_query("SELECT idTurno FROM turni WHERE idAzienda = %s", (id, ))
                turn_endpoints: List[str] = [f"http://{API_SERVER_HOST}:{API_SERVER_PORT}/api/turn/{id}" for id in turn_ids]

            # Add the turn endpoints to company dictionary
            company["turnEndpoints"] = turn_endpoints

            # Log the read operation            
            log(
                type='info',
                message=f'User {get_jwt_identity().get("email")} read company {id}',
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                origin_port=API_SERVER_PORT
            )

            # Return the companies
            return create_response(message=company, status_code=STATUS_CODES["ok"])
        except Exception as err:
            return create_response(message={'error': str(err)}, status_code=STATUS_CODES["internal_error"])

class CompanyList(Resource):
    @jwt_required_endpoint
    @check_authorization(allowed_roles=['admin', 'supertutor', 'tutor', 'teacher'])
    def get(self) -> Response:

        # Gather parameters
        anno = request.args.get('anno')
        comune = request.args.get('comune')
        settore = request.args.get('settore')
        mese = request.args.get('mese')
        materia = request.args.get('materie')

        # Gather data
        ids_batch = [] # List of ids to be used in the query

        if anno:
            ids = fetchall_query(f"SELECT idAzienda FROM turni WHERE dataInizio Like '%/{anno}'")
            ids_batch.extend(ids)

        if comune: 
            ids = fetchall_query("SELECT idAzienda FROM indirizzi WHERE comune = %s", (comune, ))
            ids_batch.extend(ids)

        if settore:
            ids = fetchall_query("SELECT A.idAzienda " \
                                 "FROM aziende AS A JOIN turni AS T ON A.idAzienda = T.idAzienda" \
                                 "JOIN turnoSettore AS TS ON TS.idTurno = T.idTurno" \
                                 "WHERE TS.settore = %s", (settore, ))
            ids_batch.extend(ids)

        if mese:
            ids = fetchall_query("SELECT A.idAzienda " \
                                 "FROM aziende AS A JOIN turni AS T" \
                                 "WHERE MONTHNAME(T.dataInizio) = %s", (mese, ))
            ids_batch.extend(ids)

        if materia:
            ids = fetchall_query("SELECT A.idAzienda " \
                                 "FROM aziende AS A JOIN turni AS T ON A.idAzienda = T.idAzienda" \
                                 "JOIN turnoMateria AS TM ON TM.idTurno = T.idTurno" \
                                 "WHERE TM.materia = %s", (materia, ))
            ids_batch.extend(ids)

        # Remove duplicates from ids_batch
        ids_batch = list(set(ids_batch))

        # Get company data
        if ids_batch:
            placeholders = ', '.join(['%s'] * len(ids_batch))
            query = (
                "SELECT A.ragioneSociale, A.codiceAteco, A.partitaIva, A.fax, A.pec, "
                "A.telefonoAzienda, A.emailAzienda, A.dataConvenzione, A.scadenzaConvenzione, "
                "A.categoria, A.indirizzoLogo, A.sitoWeb, A.formaGiuridica, I.stato, "
                "I.provincia, I.comune, I.cap, I.indirizzo "
                "FROM aziende AS A JOIN indirizzi AS I ON A.idAzienda = I.idAzienda "
                f"WHERE A.idAzienda IN ({placeholders})"
            )
            companies = fetchall_query(query, tuple(ids_batch))
        else:
            return create_response(message={'error': 'no company matches filters'}, status_code=STATUS_CODES["not_found"])

        # Return data
        return create_response(message=companies, status_code=STATUS_CODES["ok"])
        
api.add_resource(Company, f'/{BP_NAME}', f'/{BP_NAME}/<int:id>')
api.add_resource(CompanyList, f'/{BP_NAME}/list')