"""
Company Blueprint for managing companies in the database.
"""

from os.path import basename as os_path_basename
from typing import List, Dict, Any
from flask import Blueprint, request, Response
from flask_restful import Api, Resource
from marshmallow import fields, ValidationError
from marshmallow.validate import Regexp
from api_server import ma

from config import (
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
    handle_options_request,
    check_column_existence,
    get_hateos_location_string,
    jwt_validation_required,
)

# Define constants
BP_NAME = os_path_basename(__file__).replace("_bp.py", "")

# Create the blueprint and API
company_bp = Blueprint(BP_NAME, __name__)
api = Api(company_bp)


# Marshmallow schema for Company resource
class CompanySchema(ma.Schema):
    """
    Marshmallow schema for validating and deserializing company data.
    """
    ragione_sociale = fields.String(
        required=True, error_messages={"required": "ragione_sociale is required."}
    )
    codice_ateco = fields.String(
        required=True, error_messages={"required": "codice_ateco is required."}
    )
    partita_iva = fields.String(
        required=True, error_messages={"required": "partita_iva is required."}
    )
    fax = fields.String(required=True, error_messages={"required": "fax is required."})
    pec = fields.String(required=True, error_messages={"required": "pec is required."})
    telefono_azienda = fields.String(
        required=True,
        validate=Regexp(
            r"^\+?\d{1,3}\s?\d{4,14}$",
            error="telefono_azienda must be a valid international phone number",
        ),
        error_messages={"required": "telefono_azienda is required."},
    )
    email_azienda = fields.String(
        required=True, error_messages={"required": "email_azienda is required."}
    )
    data_convenzione = fields.Date(
        allow_none=True,
        error_messages={
            "invalid": "data_convenzione must be a valid date in YYYY-MM-DD format."
        },
    )
    scadenza_convenzione = fields.Date(
        allow_none=True,
        error_messages={
            "invalid": "scadenza_convenzione must be a valid date in YYYY-MM-DD format."
        },
    )
    categoria = fields.String(
        required=True, error_messages={"required": "categoria is required."}
    )
    indirizzo_logo = fields.String(
        allow_none=True,
        validate=Regexp(
            r"^(\/|https?:\/\/)[\w\-.\/]+$",
            error="indirizzo_logo must be a valid web URL or a file system path starting with '/'",
        ),
        error_messages={"invalid": "indirizzo_logo must be a string."},
    )
    sito_web = fields.URL(
        allow_none=True, error_messages={"invalid": "sito_web must be a valid URL."}
    )
    forma_giuridica = fields.String(
        allow_none=True, error_messages={"invalid": "forma_giuridica must be a string."}
    )


company_schema = CompanySchema()
company_schema_partial = CompanySchema(partial=True)


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

    ENDPOINT_PATHS = [f"/{BP_NAME}", f"/{BP_NAME}/<int:id_>"]

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor"])
    def post(self, identity) -> Response:
        """
        Create a new company in the database.
        The request body must be a JSON object with application/json content type.
        """

        # Validate and deserialize input using Marshmallow
        try:
            data = company_schema.load(request.get_json())
        except ValidationError as err:
            return create_response(
                message={"errors": err.messages},
                status_code=STATUS_CODES["bad_request"],
            )

        # Insert the company
        lastrowid, _ = execute_query(
            """INSERT INTO aziende 
            (ragione_sociale, codice_ateco, partita_iva, 
            fax, pec, telefono_azienda, email_azienda, 
            data_convenzione, scadenza_convenzione, 
            categoria, indirizzo_logo, sito_web, forma_giuridica) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                data["ragione_sociale"],
                data["codice_ateco"],
                data["partita_iva"],
                data["fax"],
                data["pec"],
                data["telefono_azienda"],
                data["email_azienda"],
                data["data_convenzione"],
                data["scadenza_convenzione"],
                data["categoria"],
                data.get("indirizzo_logo"),
                data.get("sito_web"),
                data.get("forma_giuridica"),
            ),
        )

        # Log the creation of the company
        log(
            log_type="info",
            message=f"User {identity} created company {lastrowid}",
            structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
        )

        # Return a success message
        return create_response(
            message={
                "outcome": "company successfully created",
                "location": get_hateos_location_string(bp_name=BP_NAME, id_=lastrowid),
            },
            status_code=STATUS_CODES["created"],
        )

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor"])
    def delete(self, id_, identity) -> Response:
        """
        Delete a company from the database.
        The company ID is passed as a path variable.
        """

        # Delete the company
        _, rows_affected = execute_query(
            "DELETE FROM aziende WHERE id_azienda = %s", (id_,)
        )

        # Check if any rows were affected
        if rows_affected == 0:
            return create_response(
                message={"error": "specified company does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        # Log the deletion of the company
        log(
            log_type="info",
            message=f"User {identity} deleted company {id_}",
            structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
        )

        # Return a success message
        return create_response(
            message={"outcome": "company successfully deleted"},
            status_code=STATUS_CODES["no_content"],
        )

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor"])
    def patch(self, id_, identity) -> Response:
        """
        Update a company in the database.
        The company ID is passed as a path variable.
        """

        # Validate and deserialize input using Marshmallow (partial update)
        try:
            data = company_schema_partial.load(request.get_json())
        except ValidationError as err:
            return create_response(
                message={"errors": err.messages},
                status_code=STATUS_CODES["bad_request"],
            )

        # Check if the company exists
        company: Dict[str, Any] = fetchone_query(
            "SELECT ragione_sociale FROM aziende WHERE id_azienda = %s",
            (id_,),
        )
        if company is None:
            return create_response(
                message={"outcome": "error, company does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        # Check that the specified fields actually exist in the database
        temp = check_column_existence(
            modifiable_columns=[
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
            ],
            to_modify=list(data.keys()),
        )
        if isinstance(temp, str):
            return create_response(
                message={"error": temp}, status_code=STATUS_CODES["bad_request"]
            )

        # Build the update query
        query, params = build_update_query_from_filters(
            data=data, table_name="aziende", pk_column="id_azienda", pk_value=id_
        )

        # Execute the update query
        execute_query(query, params)

        # Log the update of the company
        log(
            log_type="info",
            message=f"User {identity} updated company {id_}",
            structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
        )

        # Return a success message
        return create_response(
            message={"outcome": "company successfully updated"},
            status_code=STATUS_CODES["ok"],
        )

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def get(self, id_, identity) -> Response:
        """
        Retrieve a company from the database.
        The company ID is passed as a path variable.
        """

        try:
            # Execute the query
            company: Dict[str, Any] = fetchone_query(
                "SELECT ragione_sociale, codice_ateco, partita_iva, "
                "fax, pec, telefono_azienda, email_azienda, data_convenzione, "
                "scadenza_convenzione, categoria, indirizzo_logo, sito_web, forma_giuridica "
                "FROM aziende WHERE id_azienda = %s",
                (id_,),
            )

            # Check if the company exists
            if company is None:
                return create_response(
                    message={"error": "company not found with specified id_"},
                    status_code=STATUS_CODES["not_found"],
                )

            # Gather turn data
            turns: List[Dict[str, Any]] = fetchall_query(
                "SELECT data_inizio, data_fine, posti, posti_occupati, posti_confermati, "
                "ore, id_indirizzo, ora_inizio, ora_fine, giorno_inizio, giorno_fine "
                "FROM turni "
                "WHERE id_azienda = %s",
                (id_,),
            )

            # Add the turn endpoints to company dictionary
            company["turns"] = turns

            # Gather address data
            address_ids = [
                address["id_indirizzo"]
                for address in fetchall_query(
                    "SELECT id_indirizzo FROM indirizzi WHERE id_azienda = %s", (id_,)
                )
            ]

            # Add the address data to company dictionary
            company["address_ids"] = address_ids

            # Log the read operation
            log(
                log_type="info",
                message=f"User {identity} read company with id {id_}",
                structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
            )

            # Return the companies
            return create_response(message=company, status_code=STATUS_CODES["ok"])
        except (
            KeyError,
            ValueError,
            TypeError,
        ) as err:

            # Log the error
            log(
                log_type="error",
                message=f"Error while reading company {id_}: {str(err)}",
                structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
            )

            # Return an error response
            return create_response(
                message={"error": "internal server error"},
                status_code=STATUS_CODES["internal_error"],
            )

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def options(self) -> Response:
        """
        Handle OPTIONS requests for the resource.
        This method is used to define the allowed HTTP methods for the resource.
        """

        return handle_options_request(resource_class=self)


class CompanyList(Resource):
    """
    CompanyList resource for retrieving a list of companies from the database.
    This class handles the following HTTP methods:
    - GET: Retrieve a list of companies with optional filters
    - OPTIONS: Get allowed methods for the resource
    """

    ENDPOINT_PATHS = [f"/{BP_NAME}/list"]

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def get(self, identity) -> Response:
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
        materia: str = request.args.get("materia")

        # add limit and offset

        # Gather data

        # If all the filters are empty, return all companies
        if not any([anno, comune, settore, mese, materia]):
            companies: List[Dict[str, Any]] = fetchall_query(
                "SELECT ragione_sociale, codice_ateco, partita_iva, id_azienda,"
                "fax, pec, telefono_azienda, email_azienda, data_convenzione, "
                "scadenza_convenzione, categoria, indirizzo_logo, sito_web, forma_giuridica "
                "FROM aziende",
                (),
            )

            # Gather turn data
            for company in companies:
                # Gather turn data
                turns: List[Dict[str, Any]] = fetchall_query(
                    "SELECT data_inizio, data_fine, posti, posti_occupati, "
                    "ore, id_indirizzo, ora_inizio, ora_fine, giorno_inizio, giorno_fine, id_turno "
                    "FROM turni "
                    "WHERE id_azienda = %s",
                    (company["id_azienda"],),
                )

                # Add address data to each turn
                for turn in turns:
                    turn["addresses"] = fetchall_query(
                        "SELECT stato, provincia, comune, cap, indirizzo "
                        "FROM indirizzi "
                        "WHERE id_indirizzo = %s",
                        (turn["id_indirizzo"],),
                    )

                # Add the turn data to the company dictionary
                company["turns"] = turns

            # Log the read operation
            log(
                log_type="info",
                message=(f"User {identity} read all companies"),
                structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
            )

            # Return the companies with the turn information
            return create_response(message=companies, status_code=STATUS_CODES["ok"])

        # If filters are provided, fetch the ids of the companies that match the filters
        ids_batch: List[int] = []  # List of ids to be used in the query

        if anno:
            ids = fetchall_query(
                query="SELECT id_azienda FROM turni WHERE data_inizio LIKE %s",
                params=(f"{anno}%",),
            )
            ids_batch.extend(
                [row["id_azienda"] for row in ids]
            )  # Extract id_azienda values

        if comune:
            ids = fetchall_query(
                "SELECT id_azienda FROM indirizzi WHERE comune = %s", (comune,)
            )
            ids_batch.extend(
                [row["id_azienda"] for row in ids]
            )  # Extract id_azienda values

        if settore:
            ids = fetchall_query(
                "SELECT A.id_azienda "
                "FROM aziende AS A JOIN turni AS T ON A.id_azienda = T.id_azienda "
                "JOIN turnoSettore AS TS ON TS.id_turno = T.id_turno "
                "WHERE TS.settore = %s",
                (settore,),
            )
            ids_batch.extend(
                [row["id_azienda"] for row in ids]
            )  # Extract id_azienda values

        if mese:
            ids = fetchall_query(
                "SELECT A.id_azienda "
                "FROM aziende AS A JOIN turni AS T "
                "WHERE MONTHNAME(T.data_inizio) = %s",
                (mese,),
            )
            ids_batch.extend(
                [row["id_azienda"] for row in ids]
            )  # Extract id_azienda values

        if materia:
            ids = fetchall_query(
                "SELECT A.id_azienda "
                "FROM aziende AS A JOIN turni AS T ON A.id_azienda = T.id_azienda "
                "JOIN turnoMateria AS TM ON TM.id_turno = T.id_turno "
                "WHERE TM.materia = %s",
                (materia,),
            )
            ids_batch.extend(
                [row["id_azienda"] for row in ids]
            )  # Extract id_azienda values

        # Remove duplicates from ids_batch
        ids_batch: List[int] = list(set(ids_batch))

        # Log the read operation
        log(
            log_type="info",
            message=(
                f"User {identity} read all companies with filters:"
                f"{anno}, {comune}, {settore}, {mese}, {materia}"
            ),
            structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
        )

        # Get company data
        if ids_batch:
            placeholders: str = ", ".join(["%s"] * len(ids_batch))
            query = (
                "SELECT A.ragione_sociale, A.codice_ateco, A.partita_iva, A.fax, A.pec, "
                "A.telefono_azienda, A.email_azienda, A.data_convenzione, A.scadenza_convenzione, "
                "A.categoria, A.indirizzo_logo, A.sito_web, A.forma_giuridica, I.stato, "
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

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def options(self) -> Response:
        """
        Handle OPTIONS requests for the resource.
        This method is used to define the allowed HTTP methods for the resource.
        """

        return handle_options_request(resource_class=self)


api.add_resource(Company, *Company.ENDPOINT_PATHS)
api.add_resource(CompanyList, *CompanyList.ENDPOINT_PATHS)
