"""
This module defines the Tutor resource for managing tutor data in the API.
It includes methods for creating, deleting, updating, and retrieving tutor information.
"""

from os.path import basename as os_path_basename
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
    get_class_http_verbs,
    validate_json_request,
    get_hateos_location_string,
)

# Define constants
BP_NAME = os_path_basename(__file__).replace("_bp.py", "")

# Create the blueprint and API
tutor_bp = Blueprint(BP_NAME, __name__)
api = Api(tutor_bp)


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

    ENDPOINT_PATHS = [f"/{BP_NAME}", f"/{BP_NAME}/<int:id>"]

    @jwt_required
    @check_authorization(allowed_roles=["admin", "supertutor"])
    def post(self) -> Response:
        """
        Create a new tutor.
        The request body must be a JSON object with application/json content type.
        """

        # Validate request
        data = validate_json_request(request)
        if isinstance(data, str):
            return create_response(
                message={"error": data}, status_code=STATUS_CODES["bad_request"]
            )

        # Gather parameters
        nome: str = data.get("nome")
        cognome: str = data.get("cognome")
        telefono: str = data.get("telefono")
        email: str = data.get("email")

        # Insert the tutor
        lastrowid: int = execute_query(
            "INSERT INTO tutor (nome, cognome, telefonoTutor, emailTutor) VALUES (%s, %s, %s, %s)",
            (nome, cognome, telefono, email),
        )

        # Log the tutor creation
        log(
            log_type="info",
            message=f'User {get_jwt_identity().get("email")} created tutor {lastrowid}',
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={"endpoint": Tutor.ENDPOINT_PATHS[0], "verb": "POST"},
        )

        # Return a success message
        return create_response(
            message={
                "outcome": "tutor successfully created",
                "location": get_hateos_location_string(bp_name=BP_NAME, id_=lastrowid),
            },
            status_code=STATUS_CODES["created"],
        )

    @jwt_required
    @check_authorization(allowed_roles=["admin", "supertutor"])
    def delete(self, id_) -> Response:
        """
        Delete a tutor by ID.
        The id must be provided as a path variable.
        """

        # Check if the tutor exists
        tutor: Dict[str, Any] = fetchone_query(
            "SELECT nome FROM tutor WHERE id_tutor = %s", (id_,)
        )
        if tutor is None:
            return create_response(
                message={"error": "specified tutor does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        # Delete the tutor
        execute_query("DELETE FROM tutor WHERE id_tutor = %s", (id_,))

        # Log the deletion
        log(
            log_type="info",
            message=f'User {get_jwt_identity().get("email")} deleted tutor {id_}',
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={"endpoint": Tutor.ENDPOINT_PATHS[1], "verb": "DELETE"},
        )

        # Return a success message
        return create_response(
            message={"outcome": "tutor successfully deleted"},
            status_code=STATUS_CODES["no_content"],
        )

    @jwt_required
    @check_authorization(allowed_roles=["admin", "supertutor"])
    def patch(self, id_) -> Response:
        """
        Update a tutor by ID.
        The id must be provided as a path variable.
        """

        # Validate request
        data = validate_json_request(request)
        if isinstance(data, str):
            return create_response(
                message={"error": data}, status_code=STATUS_CODES["bad_request"]
            )

        # Check if tutor exists
        tutor: Dict[str, Any] = fetchone_query(
            "SELECT * FROM tutor WHERE id_tutor = %s", (id_,)
        )
        if tutor is None:
            return create_response(
                message={"outcome": "error, specified tutor does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        # Check that the specified fields actually exist in the database
        modifiable_columns: List[str] = [
            "nome",
            "cognome",
            "emailTutor",
            "telefonoTutor",
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
            data=data, table_name="tutor", id_column="id_tutor", id_value=id_
        )

        # Update the tutor
        execute_query(query, params)

        # Log the update
        log(
            log_type="info",
            message=f'User {get_jwt_identity().get("email")} updated tutor {id_}',
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={"endpoint": Tutor.ENDPOINT_PATHS[1], "verb": "PATCH"},
        )

        # Return a success message
        return create_response(
            message={"outcome": "tutor successfully updated"},
            status_code=STATUS_CODES["ok"],
        )

    @jwt_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def get(self, turn_id) -> Response:
        """
        Get a tutor by ID of its relative turn.
        The id must be provided as a path variable.
        """

        # Log the read
        log(
            log_type="info",
            message=(
                f"User {get_jwt_identity().get("email")} requested "
                f"tutor list with turn id {turn_id}"
            ),
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={"endpoint": Tutor.ENDPOINT_PATHS[1], "verb": "GET"},
        )

        # Check that the specified company exists
        company: Dict[str, Any] = fetchone_query(
            "SELECT * FROM aziende WHERE id_azienda = %s", (turn_id,)
        )
        if not company:
            return create_response(
                message={"outcome": "specified company not_found"},
                status_code=STATUS_CODES["not_found"],
            )

        # Get the data
        tutors: List[Dict[str, Any]] = fetchall_query(
            "SELECT TU.nome, TU.cognome, TU.emailTutor, TU.telefonoTutor "
            "FROM turni AS T JOIN turnoTutor AS TT ON T.idTurno = TT.idTurno "
            "JOIN tutor AS TU ON TU.id_tutor = TT.id_tutor "
            "WHERE T.idTurno = %s",
            (turn_id,),
        )

        # Check if query returned any results
        if not tutors:
            return create_response(
                message={"outcome": "no tutors found for specified turn"},
                status_code=STATUS_CODES["not_found"],
            )

        # Return the data
        return create_response(message=tutors, status_code=STATUS_CODES["ok"])

    @jwt_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def options(self) -> Response:
        """
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


api.add_resource(Tutor, *Tutor.ENDPOINT_PATHS)
