"""
This module defines the Tutor resource for managing tutor data in the API.
It includes methods for creating, deleting, updating, and retrieving tutor information.
"""

from os.path import basename as os_path_basename
from typing import List, Dict, Any
from flask import Blueprint, request, Response
from flask_restful import Api, Resource
from marshmallow import fields, ValidationError
from marshmallow.validate import Regexp, Range
from api_server import ma

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
    handle_options_request,
    check_column_existence,
    get_hateos_location_string,
    jwt_validation_required,
)

# Define constants
BP_NAME = os_path_basename(__file__).replace("_bp.py", "")

# Create the blueprint and API
tutor_bp = Blueprint(BP_NAME, __name__)
api = Api(tutor_bp)


# Define the schema for the request body using Marshmallow
class TutorSchema(ma.Schema):
    nome = fields.Str(
        required=True,
        error_messages={
            "required": "Nome is required.",
            "invalid": "Nome must be a string.",
        },
    )
    cognome = fields.Str(
        required=True,
        error_messages={
            "required": "Cognome is required.",
            "invalid": "Cognome must be a string.",
        },
    )
    telefono = fields.Str(
        required=True,
        validate=Regexp(
            r"^\+?\d{1,3}\s?\d{4,14}$",
            error="Telefono must be a valid international phone number",
        ),
        error_messages={
            "required": "Telefono is required.",
            "invalid": "Telefono must be a valid international phone number.",
        },
    )
    email = fields.Email(
        required=True,
        error_messages={
            "required": "Email is required.",
            "invalid": "Email must be a valid email address.",
        },
    )
    id_turno = fields.Int(
        required=True,
        validate=Range(min=1, error="ID Turno must be a positive integer"),
        error_messages={
            "required": "ID Turno is required.",
            "invalid": "ID Turno must be a positive integer.",
        },
    )


tutor_schema = TutorSchema()


class Tutor(Resource):
    """
    Tutor resource for managing tutor data.
    This class handles the following HTTP methods:
    - POST: Create a new tutor
    - DELETE: Delete a tutor by ID
    - PATCH: Update a tutor by ID
    - GET: Get a tutor by ID of its relative turn
    - OPTIONS: Get allowed HTTP methods for this endpoint
    """

    ENDPOINT_PATHS = [f"/{BP_NAME}", f"/{BP_NAME}/<int:id_>"]

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor"])
    def post(self, identity) -> Response:
        """
        Create a new tutor.
        The request body must be a JSON object with application/json content type.
        """

        # Validate and deserialize input using Marshmallow
        try:
            data = tutor_schema.load(request.get_json())
        except ValidationError as err:
            return create_response(
                message={"errors": err.messages},
                status_code=STATUS_CODES["bad_request"],
            )

        nome: str = data["nome"]
        cognome: str = data["cognome"]
        telefono: str = data["telefono"]
        email: str = data["email"]
        id_turno: int = data["id_turno"]

        # Insert the tutor
        lastrowid, _ = execute_query(
            "INSERT INTO tutor (nome, cognome, telefonoTutor, email_tutor) VALUES (%s, %s, %s, %s)",
            (nome, cognome, telefono, email),
        )

        # Insert the turno_tutor row
        _, _ = execute_query(
            "INSERT INTO turno_tutor (id_tutor, id_turno) VALUES (%s, %s)",
            (lastrowid, id_turno),
        )

        # Log the tutor creation
        log(
            log_type="info",
            message=f"User {identity} created tutor {lastrowid}",
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
        )

        # Return a success message
        return create_response(
            message={
                "outcome": "tutor successfully created",
                "location": get_hateos_location_string(bp_name=BP_NAME, id_=lastrowid),
            },
            status_code=STATUS_CODES["created"],
        )

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor"])
    def delete(self, id_, identity) -> Response:
        """
        Delete a tutor by ID.
        The id must be provided as a path variable.
        """

        # Delete the tutor
        _, rows_affected = execute_query(
            "DELETE FROM tutor WHERE id_tutor = %s", (id_,)
        )

        # Check if any rows were affected
        if rows_affected == 0:
            return create_response(
                message={"error": "specified tutor does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        # Log the deletion
        log(
            log_type="info",
            message=f"User {identity} deleted tutor {id_}",
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
        )

        # Return a success message
        return create_response(
            message={"outcome": "tutor successfully deleted"},
            status_code=STATUS_CODES["no_content"],
        )

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor"])
    def patch(self, id_, identity) -> Response:
        """
        Update a tutor by ID.
        The id must be provided as a path variable.
        """

        # Validate and deserialize input using Marshmallow (partial update)
        try:
            data = tutor_schema.load(request.get_json(), partial=True)
        except ValidationError as err:
            return create_response(
                message={"errors": err.messages},
                status_code=STATUS_CODES["bad_request"],
            )

        # Check if tutor exists using EXISTS keyword
        tutor_exists: bool = fetchone_query(
            "SELECT EXISTS(SELECT 1 FROM tutor WHERE id_tutor = %s) AS ex",
            (id_,),
        )["ex"]
        if not tutor_exists:
            return create_response(
                message={"outcome": "error, specified tutor does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        # Check that the specified fields actually exist in the database
        temp = check_column_existence(
            modifiable_columns=[
                "nome",
                "cognome",
                "email_tutor",
                "telefonoTutor",
            ],
            to_modify=list(data.keys()),
        )
        if isinstance(temp, str):
            return create_response(
                message={"error": temp}, status_code=STATUS_CODES["bad_request"]
            )

        # Build the update query
        query, params = build_update_query_from_filters(
            data=data, table_name="tutor", pk_column="id_tutor", pk_value=id_
        )

        # Update the tutor
        execute_query(query, params)

        # Log the update
        log(
            log_type="info",
            message=f"User {identity} updated tutor {id_}",
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
        )

        # Return a success message
        return create_response(
            message={"outcome": "tutor successfully updated"},
            status_code=STATUS_CODES["ok"],
        )

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def get(self, id_, identity) -> Response:
        """
        Get all the tutors associate to a given company.
        The company id must be provided as a path variable.
        """

        # Log the read
        log(
            log_type="info",
            message=(f"User {identity} requested " f"tutor list with company id {id_}"),
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
        )

        # Check that the specified company exists using EXISTS keyword
        company_exists: bool = fetchone_query(
            "SELECT EXISTS(SELECT 1 FROM aziende WHERE id_azienda = %s) AS ex",
            (id_,),
        )["ex"]
        if not company_exists:
            return create_response(
                message={"outcome": "specified company not_found"},
                status_code=STATUS_CODES["not_found"],
            )

        # Get the data
        tutors: List[Dict[str, Any]] = fetchall_query(
            """
            SELECT nome, cognome, email_tutor, telefono_tutor
            FROM tutor
            WHERE id_azienda = %s
            """,
            (id_,),
        )

        # Check if query returned any results
        if not tutors:
            return create_response(
                message={"outcome": "no tutors found for specified company"},
                status_code=STATUS_CODES["not_found"],
            )

        # Return the data
        return create_response(message=tutors, status_code=STATUS_CODES["ok"])

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def options(self) -> Response:
        """
        This method returns the allowed HTTP methods for this endpoint.
        """

        return handle_options_request(resource_class=self)


api.add_resource(Tutor, *Tutor.ENDPOINT_PATHS)
