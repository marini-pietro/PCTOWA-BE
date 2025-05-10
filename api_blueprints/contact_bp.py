"""
Blueprint for managing contacts in the database.
This module provides a RESTful API for creating, updating, deleting, and retrieving contacts.
"""

from typing import List, Dict, Any
from os.path import basename as os_path_basename
from flask import Blueprint, request, Response
from flask_restful import Api, Resource
from flask_jwt_extended import get_jwt_identity, jwt_required
from marshmallow import fields, ValidationError
from marshmallow.validate import Regexp, OneOf
from api_server import ma

from config import API_SERVER_HOST, API_SERVER_NAME_IN_LOG, STATUS_CODES, ROLES

from .blueprints_utils import (
    check_authorization,
    fetchone_query,
    execute_query,
    log,
    create_response,
    build_update_query_from_filters,
    fetchall_query,
    handle_options_request,
    check_column_existence,
    get_hateos_location_string,
)

# Define constants
BP_NAME = os_path_basename(__file__).replace("_bp.py", "")

# Create the blueprint and the API
contact_bp = Blueprint(BP_NAME, __name__)
api = Api(contact_bp)


# Marshmallow schema for Contact resource
class ContactSchema(ma.Schema):
    nome = fields.String(required=True)
    cognome = fields.String(required=True)
    telefono = fields.String(
        allow_none=True,
        validate=Regexp(
            r"^\+?\d{1,3}\s?\d{4,14}$",
            error="telefono must be a valid international phone number",
        ),
    )
    email = fields.Email(allow_none=True)
    ruolo = fields.String(
        allow_none=True,
        validate=OneOf(ROLES, error="ruolo must be one of the allowed roles"),
    )
    id_azienda = fields.Integer(required=True)


contact_schema = ContactSchema()
contact_schema_partial = ContactSchema(partial=True)


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

        # Validate and deserialize input using Marshmallow
        try:
            data = contact_schema.load(request.get_json())
        except ValidationError as err:
            return create_response(
                message={"errors": err.messages},
                status_code=STATUS_CODES["bad_request"],
            )

        # Check if azienda exists using EXISTS keyword
        company_exists: bool = fetchone_query(
            "SELECT EXISTS(SELECT 1 FROM aziende WHERE id_azienda = %s) AS exists",
            (data["id_azienda"],),
        )["exists"]
        if not company_exists:
            return create_response(
                message={"outcome": "specified company does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        # Execute query to insert the contact
        lastrowid, _ = execute_query(
            """INSERT INTO contatti 
            (nome, cognome, telefono, email, ruolo, id_azienda)
            VALUES (%s, %s, %s, %s, %s, %s)""",
            (
                data["nome"],
                data["cognome"],
                data.get("telefono"),
                data.get("email"),
                data.get("ruolo"),
                data["id_azienda"],
            ),
        )

        # Log the creation of the contact
        log(
            log_type="info",
            message=f"User {get_jwt_identity()} created contact with id_ {lastrowid}",
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
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

        # Execute query to delete the contact
        _, rows_affected = execute_query(
            "DELETE FROM contatti WHERE idContatto = %s", (id_,)
        )

        # Check if any rows were affected
        if rows_affected == 0:
            return create_response(
                message={"outcome": "specified contact not_found"},
                status_code=STATUS_CODES["not_found"],
            )

        # Log the deletion of the contact
        log(
            log_type="info",
            message=f"User {get_jwt_identity()} deleted contact {id_}",
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
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

        # Validate and deserialize input using Marshmallow (partial update)
        try:
            data = contact_schema_partial.load(request.get_json())
        except ValidationError as err:
            return create_response(
                message={"errors": err.messages},
                status_code=STATUS_CODES["bad_request"],
            )

        # Check that the specified contact exists using EXISTS keyword
        contact_exists: bool = fetchone_query(
            "SELECT EXISTS(SELECT 1 FROM contatti WHERE idContatto = %s) AS exists",
            (id_,),
        )["exists"]
        if not contact_exists:
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
            structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
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
            structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
        )

        # Check that the specified company exists using EXISTS keyword
        company_exists: bool = fetchone_query(
            "SELECT EXISTS(SELECT 1 FROM aziende WHERE id_azienda = %s) AS exists",
            (id_,),
        )["exists"]
        if not company_exists:
            return create_response(
                message={"outcome": "specified company not_found"},
                status_code=STATUS_CODES["not_found"],
            )

        # Get the data
        contact: List[Dict[str, Any]] = fetchall_query(
            "SELECT nome, cognome, telefono, email, ruolo FROM contatti WHERE id_azienda = %s",
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
