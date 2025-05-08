"""
Blueprint for managing subjects in the database.
This module provides a RESTful API for creating, deleting, updating, and retrieving subjects.
"""

from os.path import basename as os_path_basename
from typing import List, Dict, Any
from re import match as re_match
from flask import Blueprint, request, Response
from flask_restful import Api, Resource
from flask_jwt_extended import get_jwt_identity, jwt_required
from mysql.connector import IntegrityError

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
)

# Define constants
BP_NAME = os_path_basename(__file__).replace("_bp.py", "")

# Create the blueprint and API
subject_bp = Blueprint(BP_NAME, __name__)
api = Api(subject_bp)


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

    @jwt_required()
    @check_authorization(allowed_roles=["admin"])
    def post(self, materia) -> Response:
        """
        Create a new subject.
        The request body must be a JSON object with application/json content type.
        """

        # Gather parameters
        data = request.get_json()
        descrizione: str = data.get("descrizione")
        hex_color: str = data.get("hex_color")

        # Validate parameters
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
        if not isinstance(descrizione, str):
            return create_response(
                message={"error": "descrizione must be a string"},
                status_code=STATUS_CODES["bad_request"],
            )
        if len(descrizione) > 255:
            return create_response(
                message={"error": "descrizione too long"},
                status_code=STATUS_CODES["bad_request"],
            )
        if not isinstance(hex_color, str):
            return create_response(
                message={"error": "hex_color must be a string"},
                status_code=STATUS_CODES["bad_request"],
            )
        if not re_match(r"^#[0-9A-Fa-f]{6}$", hex_color):
            return create_response(
                message={"outcome": "invalid hex_color format"},
                status_code=STATUS_CODES["bad_request"],
            )

        # Insert the subject
        try:
            lastrowid, _ = execute_query(
                "INSERT INTO materie (materia, descrizione, hex_color) VALUES (%s, %s, %s)",
                (materia, descrizione, hex),
            )

            # Log the subject creation
            log(
                log_type="info",
                message=f"User {get_jwt_identity()} created subject {materia}",
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                message_id="UserAction",
                structured_data={"endpoint": Subject.ENDPOINT_PATHS[0], "verb": "POST"},
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
                    f"User {get_jwt_identity()} tried to "
                    f"create subject {materia} but it already generated {ex}"
                ),
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                message_id="UserAction",
                structured_data={"endpoint": Subject.ENDPOINT_PATHS[0], "verb": "POST"},
            )
            return create_response(
                message={"error": "conflict error"},
                status_code=STATUS_CODES["conflict"],
            )
        except (ValueError, RuntimeError) as ex:
            log(
                log_type="error",
                message=(
                    f"User {get_jwt_identity().get('email')} encountered an error "
                    f"while creating subject {materia}: {str(ex)}"
                ),
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                message_id="UserAction",
                structured_data={"endpoint": Subject.ENDPOINT_PATHS[0], "verb": "POST"},
            )
            return create_response(
                message={"error": "internal error"},
                status_code=STATUS_CODES["bad_request"],
            )

    @jwt_required()
    @check_authorization(allowed_roles=["admin"])
    def delete(self, materia) -> Response:
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
            message=f"User {get_jwt_identity()} deleted subject {materia}",
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={"endpoint": Subject.ENDPOINT_PATHS[0], "verb": "DELETE"},
        )

        # Return a success message
        return create_response(
            message={"outcome": "subject successfully deleted"},
            status_code=STATUS_CODES["no_content"],
        )

    @jwt_required()
    @check_authorization(allowed_roles=["admin"])
    def patch(self, materia) -> Response:
        """
        Update a subject.
        The request must include the subject name as a path variable.
        """

        # Gather parameters
        data = request.get_json()

        # Check that specified subject exists
        subject: Dict[str, Any] = fetchone_query(
            "SELECT descrizione FROM materie WHERE materia = %s",
            (
                materia,
            ),  # Only fetch the description to check existence (could be any field)
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
            message=f"User {get_jwt_identity()} updated subject {materia}",
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={"endpoint": Subject.ENDPOINT_PATHS[0], "verb": "PATCH"},
        )

        # Return a success message
        return create_response(
            message={"outcome": "subject successfully updated"},
            status_code=STATUS_CODES["ok"],
        )

    @jwt_required()
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def get(self) -> Response:
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
                message=f"User {get_jwt_identity()} read all subjects",
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                message_id="UserAction",
                structured_data={"endpoint": Subject.ENDPOINT_PATHS[0], "verb": "GET"},
            )

            # Return the subjects
            return create_response(message=subjects, status_code=STATUS_CODES["ok"])
        except (ValueError, RuntimeError, KeyError) as err:

            # Log the error
            log(
                log_type="error",
                message=(
                    f"User {get_jwt_identity().get('email')} encountered an error "
                    f"while reading subjects: {str(err)}"
                ),
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                message_id="UserAction",
                structured_data={"endpoint": Subject.ENDPOINT_PATHS[0], "verb": "GET"},
            )

            # Return an error response
            return create_response(
                message={"error": "internal server error"},
                status_code=STATUS_CODES["internal_error"],
            )

    @jwt_required()
    def options(self) -> Response:
        """
        Handle OPTIONS requests to provide allowed methods for the endpoint.
        """
        return handle_options_request(resource_class=self)


api.add_resource(Subject, *Subject.ENDPOINT_PATHS)
