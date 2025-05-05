"""
Blueprint for managing contacts in the database.
This module provides a RESTful API for creating, updating, deleting, and retrieving contacts.
"""

from typing import List, Dict, Any
from os.path import basename as os_path_basename
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
    execute_query,
    log,
    create_response,
    build_update_query_from_filters,
    fetchall_query,
    handle_options_request,
    validate_json_request,
    check_column_existence,
    get_hateos_location_string,
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

    ENDPOINTS_PATHS = [f"/{BP_NAME}", f"/{BP_NAME}/<int:id_>"]

    @jwt_required()
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
            "id_azienda": data.get("id_azienda"),
        }

        # Validate parameters
        if params["id_azienda"] is not None:
            try:
                params["id_azienda"] = int(params["id_azienda"])
            except (ValueError, TypeError):
                return create_response(
                    message={"outcome": "invalid company ID"},
                    status_code=STATUS_CODES["bad_request"],
                )

        # Check if azienda exists
        company: Dict[str, Any] = fetchone_query(
            "SELECT fax FROM aziende WHERE id_azienda = %s",
            (
                params["id_azienda"],
            ),  # only check existence (select column could be any)
        )
        if not company:
            return create_response(
                message={"outcome": "specified company does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        # Execute query to insert the contact
        lastrowid: int = execute_query(
            """INSERT INTO contatti 
            (nome, cognome, telefono, email, ruolo, id_azienda)
            VALUES (%s, %s, %s, %s, %s, %s)""",
            tuple(params.values()),
        )

        # Log the creation of the contact
        log(
            log_type="info",
            message=f"User {get_jwt_identity()} created contact with id_ {lastrowid}",
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={"endpoint": Contact.ENDPOINTS_PATHS[0], "verb": "POST"},
        )

        # Return a success message
        return create_response(
            message={
                "outcome": "contact created",
                "location": get_hateos_location_string(bp_name=BP_NAME, id_=lastrowid),
            },
            status_code=STATUS_CODES["created"],
        )

    @jwt_required()
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
            message=f"User {get_jwt_identity()} deleted contact {id_}",
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={"endpoint": Contact.ENDPOINTS_PATHS[1], "verb": "DELETE"},
        )

        # Return a success message
        return create_response(
            message={"outcome": "contact successfully deleted"},
            status_code=STATUS_CODES["no_content"],
        )

    @jwt_required()
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
            "SELECT nome FROM contatti WHERE idContatto = %s",
            (id_,),  # Only fetch the province to check existence (could be any field)
        )
        if contact is None:
            return create_response(
                message={"outcome": "specified contact not_found"},
                status_code=STATUS_CODES["not_found"],
            )

        # Check that the specified fields actually exist in the database
        temp = check_column_existence(
            modifiable_columns=[
                "nome",
                "cognome",
                "telefono",
                "email",
                "ruolo",
                "id_azienda",
            ],
            to_modify=list(data.keys()),
        )
        if isinstance(temp, str):
            return create_response(
                message={"error": temp}, status_code=STATUS_CODES["bad_request"]
            )

        # Build the update query
        query, params = build_update_query_from_filters(
            data=data, table_name="contatti", pk_column="idContatto", pk_value=id_
        )

        # Execute the update query
        execute_query(query, params)

        # Log the update of the contact
        log(
            log_type="info",
            message=f"User {get_jwt_identity()} updated contact {id_}",
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={"endpoint": Contact.ENDPOINTS_PATHS[1], "verb": "PATCH"},
        )

        # Return a success message
        return create_response(
            message={"outcome": "contact successfully updated"},
            status_code=STATUS_CODES["ok"],
        )

    @jwt_required()
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def get(self, id_) -> Response:
        """
        Get a contact by the ID of its company.
        The id is passed as a path variable.
        """

        # Log the request
        log(
            log_type="info",
            message=(
                f"User {get_jwt_identity()} requested "
                f"contact list for company with id {id_}"
            ),
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={"endpoint": Contact.ENDPOINTS_PATHS[0], "verb": "GET"},
        )

        # Check that the specified company exists
        company: Dict[str, Any] = fetchone_query(
            "SELECT fax FROM aziende WHERE id_azienda = %s",
            (id_,),  # Only fetch the name to check existence (could be any field)
        )
        if not company:
            return create_response(
                message={"outcome": "specified company not_found"},
                status_code=STATUS_CODES["not_found"],
            )

        # Get the data
        contact: List[Dict[str, Any]] = fetchall_query(
            "SELECT nome FROM contatti WHERE id_azienda = %s",
            (id_,),  # Only fetch the name (select column could be any field)
        )

        # Check if query returned any results
        if not contact:
            return create_response(
                message={"outcome": "no contacts found for the specified company"},
                status_code=STATUS_CODES["not_found"],
            )

        # Return the contact data
        return create_response(message=contact, status_code=STATUS_CODES["ok"])

    @jwt_required()
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def options(self) -> Response:
        """
        Handle OPTIONS requests for CORS preflight checks.
        This method returns the allowed HTTP methods for this endpoint.
        """
        return handle_options_request(resource_class=self)


api.add_resource(Contact, *Contact.ENDPOINTS_PATHS)
