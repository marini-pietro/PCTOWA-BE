"""
Company Blueprint for managing companies in the database.
"""

from os.path import basename as os_path_basename
from re import match as re_match
from typing import List, Dict, Any
from flask import Blueprint, request, Response
from flask_restful import Api, Resource
from flask_jwt_extended import get_jwt_identity, jwt_required

from config import (
    API_SERVER_HOST,
    API_SERVER_NAME_IN_LOG,
    STATUS_CODES,
)

from .blueprints_utils import (
    check_authorization,
    fetchone_query,
    fetchall_query,
    execute_query,
    log,
    create_response,
    build_update_query_from_filters,
    parse_date_string,
    get_class_http_verbs,
    validate_json_request,
    get_hateos_location_string,
)

# Define constants
BP_NAME = os_path_basename(__file__).replace("_bp.py", "")

# Create the blueprint and API
company_bp = Blueprint(BP_NAME, __name__)
api = Api(company_bp)


class Company(Resource):
    """
    Company resource for managing companies in the database.
    This class handles the following HTTP methods:
    - POST: Create a new company
    - DELETE: Delete a company by ID
    - PATCH: Update a company by ID
    - GET: Retrieve a company by ID
    - OPTIONS: Get allowed methods for the resource
    """

    ENDPOINT_PATHS = [f"/{BP_NAME}", f"/{BP_NAME}/<int:id>"]

    @jwt_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor"])
    def post(self) -> Response:
        """
        Create a new company in the database.
        The request body must be a JSON object with application/json content log_type.
        """

        # Validate request
        data = validate_json_request(request)
        if isinstance(data, str):
            return create_response(
                message={"error": data}, status_code=STATUS_CODES["bad_request"]
            )

        # Gather parameters from the request body
        # (new dictionary is necessary so that user can provide JSON with fields in any order)
        params: Dict[str, str] = {
            "ragioneSociale": data.get("ragioneSociale"),
            "nome": data.get("nome"),
            "sitoWeb": data.get("sitoWeb"),
            "indirizzoLogo": data.get("indirizzoLogo"),
            "codiceAteco": data.get("codiceAteco"),
            "partitaIVA": data.get("partitaIVA"),
            "telefonoAzienda": data.get("telefonoAzienda"),
            "fax": data.get("fax"),
            "emailAzienda": data.get("emailAzienda"),
            "pec": data.get("pec"),
            "formaGiuridica": data.get("formaGiuridica"),
            "dataConvenzione": parse_date_string(data.get("dataConvenzione")),
            "scadenzaConvenzione": parse_date_string(data.get("scadenzaConvenzione")),
            "settore": data.get("settore"),
            "categoria": data.get("categoria"),
        }

        # Validate parameters
        if not re_match(r"^\+\d{1,3}\s?\d{4,14}$", params["telefonoAzienda"]):
            return create_response(
                message={"error": "invalid phone number format"},
                status_code=STATUS_CODES["bad_request"],
            )

        # TODO: add regex check to all the other fields

        lastrowid: int = execute_query(
            """INSERT INTO aziende 
            (ragioneSociale, nome, sitoWeb, indirizzoLogo, codiceAteco, 
             partitaIVA, telefonoAzienda, fax, emailAzienda, pec, 
             formaGiuridica, dataConvenzione, scadenzaConvenzione, settore, categoria) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            params.values(),
        )

        # Log the creation of the company
        log(
            log_type="info",
            message=f'User {get_jwt_identity().get("email")} created company {lastrowid}',
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={"endpoint": {Company.ENDPOINT_PATHS[0]}, "verb": "POST"},
        )

        # Return a success message
        return create_response(
            message={
                "outcome": "company successfully created",
                "location": get_hateos_location_string(bp_name=BP_NAME, id_=lastrowid),
            },
            status_code=STATUS_CODES["created"],
        )

    @jwt_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor"])
    def delete(self, id_) -> Response:
        """
        Delete a company from the database.
        The company ID is passed as a path variable.
        """

        # Check if specified company exists
        company: Dict[str, Any] = fetchone_query(
            "SELECT ragioneSociale FROM aziende WHERE id_azienda = %s", (id_,)
        )  # Only fetch the province to check existence (could be any field)
        if not company:
            return create_response(
                message={"error": "specified company does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        # Delete the company
        execute_query("DELETE FROM aziende WHERE id_azienda = %s", (id_,))

        # Log the deletion of the company
        log(
            log_type="info",
            message=f'User {get_jwt_identity().get("email")} deleted company {id_}',
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={"endpoint": {Company.ENDPOINT_PATHS[1]}, "verb": "DELETE"},
        )

        # Return a success message
        return create_response(
            message={"outcome": "company successfully deleted"},
            status_code=STATUS_CODES["no_content"],
        )

    @jwt_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor"])
    def patch(self, id_) -> Response:
        """
        Update a company in the database.
        The company ID is passed as a path variable.
        """

        # Validate request
        data = validate_json_request(request)
        if isinstance(data, str):
            return create_response(
                message={"error": data}, status_code=STATUS_CODES["bad_request"]
            )

        # Gather data
        to_modify: List[str] = list(data.keys())

        # Check if the company exists
        company: Dict[str, Any] = fetchone_query(
            "SELECT * FROM aziende WHERE id_azienda = %s", (id_,)
        )
        if not company:
            return create_response(
                message={"outcome": "error, company does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        # Check that the specified fields actually exist in the database
        modifiable_columns: List[str] = [
            "ragione_sociale",
            "codice_ateco",
            "partita_iva",
            "fax",
            "pec",
            "telefono_azienda",
            "email_azienda",
            "data_convenzione",
            "scadenza_convenzione",
            "categoria",
            "indirizzo_logo",
            "sito_web",
            "forma_giuridica",
        ]
        error_columns: List[str] = [
            field for field in to_modify if field not in modifiable_columns
        ]
        if error_columns:
            return create_response(
                message={
                    "outcome": f"error, field(s) {error_columns} do not exist or cannot be modified"
                },
                status_code=STATUS_CODES["bad_request"],
            )

        # Build the update query
        query, params = build_update_query_from_filters(
            data=data, table_name="aziende", id_column="id_azienda", id_value=id_
        )

        # Execute the update query
        execute_query(query, params)

        # Log the update of the company
        log(
            log_type="info",
            message=f'User {get_jwt_identity().get("email")} updated company {id_}',
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={"endpoint": {Company.ENDPOINT_PATHS[1]}, "verb": "PATCH"},
        )

        # Return a success message
        return create_response(
            message={"outcome": "company successfully updated"},
            status_code=STATUS_CODES["ok"],
        )

    @jwt_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def get(self, id_) -> Response:
        """
        Retrieve a company from the database.
        The company ID is passed as a path variable.
        """

        try:
            # Execute the query
            company: Dict[str, Any] = fetchone_query(
                "SELECT * FROM aziende WHERE = %s", (id_,)
            )

            # Check if the company exists
            if not company:
                return create_response(
                    message={"error": "company not found with specified id_"},
                    status_code=STATUS_CODES["not_found"],
                )

            # Gather turn data
            turns: List[Dict[str, Any]] = fetchall_query(
                "SELECT data_inizio, data_fine, posti, posti_occupati, "
                "ore, id_indirizzo, ora_inizio, ora_fine, giorno_inizio, giorno_fine "
                "FROM turni "
                "WHERE id_azienda = %s",
                (id_,),
            )

            # Add the turn endpoints to company dictionary
            company["turns"] = turns

            # Gather address data
            addresses: List[Dict[str, Any]] = fetchall_query(
                "SELECT stato,provincia,comune,cap,indirizzo FROM indirizzi WHERE id_azienda = %s",
                (id_,),
            )

            # Add the address data to company dictionary
            company["addresses"] = addresses

            # Log the read operation
            log(
                log_type="info",
                message=f'User {get_jwt_identity().get("email")} read company {id_}',
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                message_id="UserAction",
                structured_data={
                    "endpoint": {Company.ENDPOINT_PATHS[1]},
                    "verb": "GET",
                },
            )

            # Return the companies
            return create_response(message=company, status_code=STATUS_CODES["ok"])
        except (
            KeyError,
            ValueError,
            TypeError,
        ) as err:  # Replace with specific exceptions

            # Log the error
            log(
                log_type="error",
                message=f"Error while reading company {id_}: {str(err)}",
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                message_id="UserAction",
                structured_data={
                    "endpoint": {Company.ENDPOINT_PATHS[1]},
                    "verb": "GET",
                },
            )

            # Return an error response
            return create_response(
                message={"error": "interal server error"},
                status_code=STATUS_CODES["internal_error"],
            )

    @jwt_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def options(self) -> Response:
        """
        Handle OPTIONS requests for the resource.
        This method is used to define the allowed HTTP methods for the resource.
        """

        # Define allowed methods
        allowed_methods = get_class_http_verbs(type(self))

        # Create the response
        response = Response(status=STATUS_CODES["ok"])
        response.headers["Allow"] = ", ".join(allowed_methods)
        response.headers["Access-Control-Allow-Origin"] = (
            "*"  # Adjust as needed for CORS
        )
        response.headers["Access-Control-Allow-Methods"] = ", ".join(allowed_methods)
        response.headers["Access-Control-Allow-Headers"] = (
            "Content-log_type, Authorization"
        )

        return response


class CompanyList(Resource):
    """
    CompanyList resource for retrieving a list of companies from the database.
    This class handles the following HTTP methods:
    - GET: Retrieve a list of companies with optional filters
    - OPTIONS: Get allowed methods for the resource
    """

    ENDPOINT_PATHS = [f"/{BP_NAME}/list"]

    @jwt_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def get(self) -> Response:
        """
        Retrieve a list of companies from the database.
        The request can include filters for the following fields:
        - anno: Year of the start date of the shifts
        - comune: Municipality of the address
        - settore: Sector of the shifts
        - mese: Month of the start date of the shifts
        - materia: Subject of the shifts
        """

        # Gather parameters
        anno: str = request.args.get("anno")
        comune: str = request.args.get("comune")
        settore: str = request.args.get("settore")
        mese: str = request.args.get("mese")
        materia: str = request.args.get("materie")

        # Gather data
        ids_batch: List[int] = []  # List of ids to be used in the query
        if anno:
            ids = fetchall_query(
                query="SELECT id_azienda FROM turni WHERE data_inizio Like '%/%s'",
                params=(anno,),
            )
            ids_batch.extend(ids)

        if comune:
            ids = fetchall_query(
                "SELECT id_azienda FROM indirizzi WHERE comune = %s", (comune,)
            )
            ids_batch.extend(ids)

        if settore:
            ids = fetchall_query(
                "SELECT A.id_azienda "
                "FROM aziende AS A JOIN turni AS T ON A.id_azienda = T.id_azienda "
                "JOIN turnoSettore AS TS ON TS.idTurno = T.idTurno "
                "WHERE TS.settore = %s",
                (settore,),
            )
            ids_batch.extend(ids)

        if mese:
            ids = fetchall_query(
                "SELECT A.id_azienda "
                "FROM aziende AS A JOIN turni AS T "
                "WHERE MONTHNAME(T.data_inizio) = %s",
                (mese,),
            )
            ids_batch.extend(ids)

        if materia:
            ids = fetchall_query(
                "SELECT A.id_azienda "
                "FROM aziende AS A JOIN turni AS T ON A.id_azienda = T.id_azienda "
                "JOIN turnoMateria AS TM ON TM.idTurno = T.idTurno "
                "WHERE TM.materia = %s",
                (materia,),
            )
            ids_batch.extend(ids)

        # Remove duplicates from ids_batch
        ids_batch: List[int] = list(set(ids_batch))

        # Log the read operation
        log(
            log_type="info",
            message=(
                f"User {get_jwt_identity().get("email")} read companies with filters:"
                f"{anno}, {comune}, {settore}, {mese}, {materia}"
            ),
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={
                "endpoint": {CompanyList.ENDPOINT_PATHS[0]},
                "verb": "GET",
            },
        )

        # Get company data
        if ids_batch:
            placeholders: str = ", ".join(["%s"] * len(ids_batch))
            query = (
                "SELECT A.ragioneSociale, A.codiceAteco, A.partitaIva, A.fax, A.pec, "
                "A.telefonoAzienda, A.emailAzienda, A.dataConvenzione, A.scadenzaConvenzione, "
                "A.categoria, A.indirizzoLogo, A.sitoWeb, A.formaGiuridica, I.stato, "
                "I.provincia, I.comune, I.cap, I.indirizzo "
                "FROM aziende AS A JOIN indirizzi AS I ON A.id_azienda = I.id_azienda "
                f"WHERE A.id_azienda IN ({placeholders})"
            )
            companies: List[Dict[str, Any]] = fetchall_query(query, tuple(ids_batch))
        else:
            return create_response(
                message={"error": "no company matches filters"},
                status_code=STATUS_CODES["not_found"],
            )

        # Return data
        return create_response(message=companies, status_code=STATUS_CODES["ok"])

    @jwt_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def options(self) -> Response:
        """
        Handle OPTIONS requests for the resource.
        This method is used to define the allowed HTTP methods for the resource.
        """

        # Define allowed methods
        allowed_methods = get_class_http_verbs(type(self))

        # Create the response
        response = Response(status=STATUS_CODES["ok"])
        response.headers["Allow"] = ", ".join(allowed_methods)
        response.headers["Access-Control-Allow-Origin"] = (
            "*"  # Adjust as needed for CORS
        )
        response.headers["Access-Control-Allow-Methods"] = ", ".join(allowed_methods)
        response.headers["Access-Control-Allow-Headers"] = (
            "Content-log_type, Authorization"
        )

        return response


api.add_resource(Company, *Company.ENDPOINT_PATHS)
api.add_resource(CompanyList, *CompanyList.ENDPOINT_PATHS)
