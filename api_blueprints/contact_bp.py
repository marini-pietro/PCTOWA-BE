from os.path import basename as os_path_basename
from flask import Blueprint, request, Response
from flask_restful import Api, Resource
from flask_jwt_extended import get_jwt_identity
from typing import List, Dict, Union, Any
from .blueprints_utils import (
    check_authorization,
    fetchone_query,
    execute_query,
    log,
    jwt_required_endpoint,
    create_response,
    build_update_query_from_filters,
    fetchall_query,
    get_class_http_verbs,
    validate_json_request,
)
from config import (
    API_SERVER_HOST,
    API_SERVER_PORT,
    API_SERVER_NAME_IN_LOG,
    STATUS_CODES,
)

# Define constants
BP_NAME = os_path_basename(__file__).replace("_bp.py", "")

# Create the blueprint and the API
contact_bp = Blueprint(BP_NAME, __name__)
api = Api(contact_bp)


class Contact(Resource):
    """
    Contact resource for managing contacts in the database.
    """

    ENDPOINTS_PATHS = [f"/{BP_NAME}", f"/{BP_NAME}/<int:id>"]

    @jwt_required_endpoint
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor"])
    def post(self) -> Response:
        """
        Create a new contact.
        The request must contain a JSON body with application/json.
        """

        # Validate request
        data = validate_json_request(request)
        if isinstance(data, str):
            return create_response(
                message={"error": data}, status_code=STATUS_CODES["bad_request"]
            )

        # Gather parameters
        params: Dict[str, str] = {
            "nome": data.get("nome"),
            "cognome": data.get("cognome"),
            "telefono": data.get("telefono"),
            "email": data.get("email"),
            "ruolo": data.get("ruolo"),
            "idAzienda": data.get("idAzienda"),
        }

        # Validate parameters
        if params["idAzienda"] is not None:
            try:
                params["idAzienda"] = int(params["idAzienda"])
            except (ValueError, TypeError):
                return create_response(
                    message={"outcome": "invalid company ID"},
                    status_code=STATUS_CODES["bad_request"],
                )

        # Check if azienda exists
        company: Dict[str, Any] = fetchone_query(
            "SELECT * FROM aziende WHERE idAzienda = %s", (params["idAzienda"],)
        )
        if not company:
            return create_response(
                message={"outcome": "specified company does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        # Execute query to insert the contact
        lastrowid: int = execute_query(
            """INSERT INTO contatti 
            (nome, cognome, telefono, email, ruolo, idAzienda)
            VALUES (%s, %s, %s, %s, %s, %s)""",
            tuple(params.values()),
        )

        # Log the creation of the contact
        log(
            log_type="info",
            message=f'User {get_jwt_identity().get("email")} created contact with id_ {lastrowid}',
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            structured_data=f"[{Contact.ENDPOINTS_PATHS[0]} Verb POST]",
        )

        # Return a success message
        return create_response(
            message={
                "outcome": "contact created",
                "location": f"http://{API_SERVER_HOST}:{API_SERVER_PORT}/api/{BP_NAME}/{lastrowid}",
            },
            status_code=STATUS_CODES["created"],
        )

    @jwt_required_endpoint
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor"])
    def delete(self, id_) -> Response:
        """
        Delete a contact.
        The id is passed as a path variable.
        """

        # Check that the specified contact exists
        contact: Dict[str, Any] = fetchone_query(
            "SELECT nome FROM contatti WHERE idContatto = %s", (id_,)
        )  # Only fetch the province to check existence (could be any field)
        if not contact:
            return create_response(
                message={"outcome": "specified contact not_found"},
                status_code=STATUS_CODES["not_found"],
            )

        # Execute query to delete the contact
        execute_query("DELETE FROM contatti WHERE idContatto = %s", (id_,))

        # Log the deletion of the contact
        log(
            log_type="info",
            message=f'User {get_jwt_identity().get("email")} deleted contact {id_}',
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            structured_data=f"[{Contact.ENDPOINTS_PATHS[1]} Verb DELETE]",
        )

        # Return a success message
        return create_response(
            message={"outcome": "contact successfully deleted"},
            status_code=STATUS_CODES["no_content"],
        )

    @jwt_required_endpoint
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor"])
    def patch(self, id_) -> Response:
        """
        Update a contact.
        The id is passed as a path variable.
        """

        # Validate request
        data = validate_json_request(request)
        if isinstance(data, str):
            return create_response(
                message={"error": data}, status_code=STATUS_CODES["bad_request"]
            )

        # Check that the specified contact exists
        contact: Dict[str, Any] = fetchone_query(
            "SELECT * FROM contatti WHERE idContatto = %s", (id_,)
        )
        if not contact:
            return create_response(
                message={"outcome": "specified contact not_found"},
                status_code=STATUS_CODES["not_found"],
            )

        # Check that the specified fields actually exist in the database
        modifiable_columns: List[str] = [
            "nome",
            "cognome",
            "telefono",
            "email",
            "ruolo",
            "idAzienda",
        ]
        to_modify: List[str] = list(data.keys())
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
            data=data, table_name="contatti", id_column="idContatto", id_value=id_
        )

        # Execute the update query
        execute_query(query, params)

        # Log the update of the contact
        log(
            log_type="info",
            message=f'User {get_jwt_identity().get("email")} updated contact {id_}',
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            structured_data=f"[{Contact.ENDPOINTS_PATHS[1]} Verb PATCH]",
        )

        # Return a success message
        return create_response(
            message={"outcome": "contact successfully updated"},
            status_code=STATUS_CODES["ok"],
        )

    @jwt_required_endpoint
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def get(self, company_id) -> Response:
        """
        Get a contact by the ID of its company.
        The id is passed as a path variable.
        """

        # Log the request
        log(
            log_type="info",
            message=f'User {get_jwt_identity().get("email")} requested contact list for company {company_id}',
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            structured_data=f"[{Contact.ENDPOINTS_PATHS[1]} Verb GET]",
        )

        # Check that the specified company exists
        company: Dict[str, Any] = fetchone_query(
            "SELECT * FROM aziende WHERE idAzienda = %s", (company_id,)
        )
        if not company:
            return create_response(
                message={"outcome": "specified company not_found"},
                status_code=STATUS_CODES["not_found"],
            )

        # Get the data
        contact: List[Dict[str, Any]] = fetchall_query(
            "SELECT * FROM contatti WHERE idAzienda = %s", (company_id,)
        )

        # Check if query returned any results
        if not contact:
            return create_response(
                message={"outcome": "no contacts found for the specified company"},
                status_code=STATUS_CODES["not_found"],
            )

        # Return the contact data
        return create_response(message=contact, status_code=STATUS_CODES["ok"])

    @jwt_required_endpoint
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def options(self) -> Response:
        """
        Handle OPTIONS requests for CORS preflight checks.
        This method returns the allowed HTTP methods for this endpoint.
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
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"

        return response


api.add_resource(Contact, *Contact.ENDPOINTS_PATHS)
