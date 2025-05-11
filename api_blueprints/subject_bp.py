"""
Blueprint for managing subjects in the database.
This module provides a RESTful API for creating, deleting, updating, and retrieving subjects.
"""

from os.path import basename as os_path_basename
from typing import List, Dict, Any
from flask import Blueprint, request, Response
from flask_restful import Api, Resource
from marshmallow import fields, ValidationError
from mysql.connector import IntegrityError
from marshmallow.validate import Regexp
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
subject_bp = Blueprint(BP_NAME, __name__)
api = Api(subject_bp)


# Marshmallow schema for Subject resource
class SubjectSchema(ma.Schema):
    descrizione = fields.String(
        required=True, error_messages={"required": "descrizione is required."}
    )
    hex_color = fields.String(
        required=True,
        validate=Regexp(
            r"^#[0-9A-Fa-f]{6}$",
            error="hex_color must be a valid hex color (e.g. #AABBCC)",
        ),
        error_messages={
            "required": "hex_color is required.",
            "invalid": "hex_color must be a valid hex color (e.g. #AABBCC).",
        },
    )


subject_schema = SubjectSchema()
subject_schema_partial = SubjectSchema(partial=True)


class Subject(Resource):
    """
    Subject resource for managing subjects in the database.
    This class handles the following HTTP methods:
    - POST: Create a new subject
    - DELETE: Delete a subject
    - PATCH: Update a subject
    - GET: Get all subjects with pagination
    - OPTIONS: Get allowed methods for the endpoint
    """

    ENDPOINT_PATHS = [f"/{BP_NAME}/<string:materia>"]

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin"])
    def post(self, materia, identity) -> Response:
        """
        Create a new subject.
        The request body must be a JSON object with application/json content type.
        """

        # Validate and deserialize input using Marshmallow
        try:
            data = subject_schema.load(request.get_json())
        except ValidationError as err:
            return create_response(
                message={"errors": err.messages},
                status_code=STATUS_CODES["bad_request"],
            )

        descrizione: str = data["descrizione"]
        hex_color: str = data["hex_color"]

        # Additional validation for materia
        if not isinstance(materia, str):
            return create_response(
                message={"error": "materia must be a string"},
                status_code=STATUS_CODES["bad_request"],
            )
        if len(materia) > 255:
            return create_response(
                message={"error": "materia too long"},
                status_code=STATUS_CODES["bad_request"],
            )
        if len(descrizione) > 255:
            return create_response(
                message={"error": "descrizione too long"},
                status_code=STATUS_CODES["bad_request"],
            )

        # Insert the subject
        try:
            lastrowid, _ = execute_query(
                "INSERT INTO materie (materia, descrizione, hex_color) VALUES (%s, %s, %s)",
                (materia, descrizione, hex_color),
            )

            # Log the subject creation
            log(
                log_type="info",
                message=f"User {identity} created subject {materia}",
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                message_id="UserAction",
                structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
            )

            # Return a success message
            return create_response(
                message={
                    "outcome": "subject successfully created",
                    "location": get_hateos_location_string(
                        bp_name=BP_NAME, id_=lastrowid
                    ),
                },
                status_code=STATUS_CODES["created"],
            )

        except IntegrityError as ex:
            log(
                log_type="error",
                message=(
                    f"User {identity} tried to "
                    f"create subject {materia} but it already generated {ex}"
                ),
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                message_id="UserAction",
                structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
            )
            return create_response(
                message={"error": "conflict error"},
                status_code=STATUS_CODES["conflict"],
            )
        except (ValueError, RuntimeError) as ex:
            log(
                log_type="error",
                message=(
                    f"User {identity.get('email')} encountered an error "
                    f"while creating subject {materia}: {str(ex)}"
                ),
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                message_id="UserAction",
                structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
            )
            return create_response(
                message={"error": "internal error"},
                status_code=STATUS_CODES["bad_request"],
            )

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin"])
    def delete(self, materia, identity) -> Response:
        """
        Delete a subject.
        The request must include the subject name as a path variable.
        """

        # Delete the subject
        _, rows_affected = execute_query(
            "DELETE FROM materie WHERE materia = %s", (materia,)
        )

        # Check if any rows were affected
        if rows_affected == 0:
            return create_response(
                message={"error": "specified subject does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        # Log the deletion
        log(
            log_type="info",
            message=f"User {identity} deleted subject {materia}",
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
        )

        # Return a success message
        return create_response(
            message={"outcome": "subject successfully deleted"},
            status_code=STATUS_CODES["no_content"],
        )

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin"])
    def patch(self, materia, identity) -> Response:
        """
        Update a subject.
        The request must include the subject name as a path variable.
        """

        # Validate and deserialize input using Marshmallow (partial update)
        try:
            data = subject_schema_partial.load(request.get_json())
        except ValidationError as err:
            return create_response(
                message={"errors": err.messages},
                status_code=STATUS_CODES["bad_request"],
            )

        # Check that specified subject exists
        subject: Dict[str, Any] = fetchone_query(
            "SELECT descrizione FROM materie WHERE materia = %s",
            (materia,),
        )
        if subject is None:
            return create_response(
                message={"outcome": "error, specified subject does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        # Check that the specified fields actually exist in the database
        temp = check_column_existence(
            modifiable_columns=["materia", "descrizione", "hex_color"],
            to_modify=list(data.keys()),
        )
        if isinstance(temp, str):
            return create_response(
                message={"outcome": temp},
                status_code=STATUS_CODES["bad_request"],
            )

        # Build the query
        query, params = build_update_query_from_filters(
            data=data, table_name="materie", pk_column="materia", pk_value=materia
        )

        # Update the subject
        execute_query(query, params)

        # Log the update
        log(
            log_type="info",
            message=f"User {identity} updated subject {materia}",
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
        )

        # Return a success message
        return create_response(
            message={"outcome": "subject successfully updated"},
            status_code=STATUS_CODES["ok"],
        )

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def get(self, identity) -> Response:
        """
        Get all subjects with pagination.
        The request can include limit and offset as query parameters.
        """

        # Gather parameters
        limit: int = request.args.get("limit", default=10, type=int)
        offset: int = request.args.get("offset", default=0, type=int)

        # Validate parameters
        if limit < 0 or offset < 0:
            return create_response(
                message={"error": "limit and offset must be non-negative integers"},
                status_code=STATUS_CODES["bad_request"],
            )

        try:
            # Execute query
            subjects = fetchall_query(
                "SELECT materia, descrizione, hex_color FROM materie LIMIT %s OFFSET %s",
                params=(limit, offset),
            )

            # Log the read
            log(
                log_type="info",
                message=f"User {identity} read all subjects",
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                message_id="UserAction",
                structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
            )

            # Return the subjects
            return create_response(message=subjects, status_code=STATUS_CODES["ok"])
        except (ValueError, RuntimeError, KeyError) as err:

            # Log the error
            log(
                log_type="error",
                message=(
                    f"User {identity.get('email')} encountered an error "
                    f"while reading subjects: {str(err)}"
                ),
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                message_id="UserAction",
                structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
            )

            # Return an error response
            return create_response(
                message={"error": "internal server error"},
                status_code=STATUS_CODES["internal_error"],
            )

    @jwt_validation_required
    def options(self) -> Response:
        """
        Handle OPTIONS requests to provide allowed methods for the endpoint.
        """
        return handle_options_request(resource_class=self)


api.add_resource(Subject, *Subject.ENDPOINT_PATHS)
