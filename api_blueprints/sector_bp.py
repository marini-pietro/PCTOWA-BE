"""
Blueprint for managing sectors in the database.
This module provides a RESTful API for creating, deleting, updating, and retrieving sectors.
It also includes authorization checks and logging for each operation.
"""

from os.path import basename as os_path_basename
from typing import Dict, List, Any
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
    get_class_http_verbs,
    validate_json_request,
    get_hateos_location_string,
)

# Define constants
BP_NAME = os_path_basename(__file__).replace("_bp.py", "")

# Create the blueprint and API
sector_bp = Blueprint(BP_NAME, __name__)
api = Api(sector_bp)


class Sector(Resource):
    """
    Sector resource for managing sectors in the database.
    This class handles the following HTTP methods:
    - POST: Create a new sector
    - DELETE: Delete a sector
    - PATCH: Update a sector
    - GET: Get all sectors with pagination
    - OPTIONS: Get allowed methods for the resource
    """

    ENDPOINT_PATHS = [f"/{BP_NAME}", f"{BP_NAME}/<string:settore>"]

    @jwt_required()
    @check_authorization(allowed_roles=["admin"])
    def post(self) -> Response:
        """
        Create a new sector.
        The request body must be a JSON object with application/json content type.
        """

        # Validate request
        data = validate_json_request(request)
        if isinstance(data, str):
            return create_response(
                message={"error": data}, status_code=STATUS_CODES["bad_request"]
            )

        # Gather parameters
        settore: str = data.get("settore")

        # Validate parameters
        if settore is None or len(settore) == 0:
            return create_response(
                message={"error": "settore parameter is required"},
                status_code=STATUS_CODES["bad_request"],
            )
        if len(settore) > 255:
            return create_response(
                message={"error": "settore parameter is too long"},
                status_code=STATUS_CODES["bad_request"],
            )
        if not isinstance(settore, str):
            return create_response(
                message={"error": "settore parameter must be a string"},
                status_code=STATUS_CODES["bad_request"],
            )

        try:
            # Insert the sector
            lastrowid: int = execute_query(
                "INSERT INTO settori (settore) VALUES (%s)", (settore,)
            )
        except IntegrityError as ex:
            log(
                log_type="error",
                message=(
                    f"User {get_jwt_identity()} tried "
                    f"to create sector {settore} but it generated {ex}"
                ),
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                message_id="UserAction",
                structured_data={"endpoint": Sector.ENDPOINT_PATHS[0], "verb": "POST"},
            )
            return create_response(
                message={"error": "conflict error"},
                status_code=STATUS_CODES["conflict"],
            )
        except (ValueError, TypeError) as ex:
            log(
                log_type="error",
                message=(
                    f"User {get_jwt_identity()} failed to "
                    f"create sector {settore} with error: {str(ex)}"
                ),
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                message_id="UserAction",
                structured_data={"endpoint": Sector.ENDPOINT_PATHS[0], "verb": "POST"},
            )
            return create_response(
                message={"error": "internal server error"},
                status_code=STATUS_CODES["internal_error"],
            )

        # Log the sector creation
        log(
            log_type="info",
            message=f"User {get_jwt_identity()} created sector {settore}",
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={"endpoint": Sector.ENDPOINT_PATHS[0], "verb": "POST"},
        )

        # Return a success message
        return create_response(
            message={
                "outcome": "sector successfully created",
                "location": get_hateos_location_string(bp_name=BP_NAME, id_=lastrowid),
            },
            status_code=STATUS_CODES["created"],
        )

    @jwt_required()
    @check_authorization(allowed_roles=["admin"])
    def delete(self, settore) -> Response:
        """
        Delete a sector.
        The request must include the sector name as a path variable.
        """

        # Check if sector exists
        sector: Dict[str, Any] = fetchone_query(
            "SELECT settore FROM settori WHERE settore = %s", (settore,)
        )  # Only fetch the province to check existence (could be any field)
        if sector is None:
            return {"error": "specified sector does not exist"}, STATUS_CODES[
                "not_found"
            ]

        # Delete the sector
        execute_query("DELETE FROM settori WHERE settore = %s", (settore,))

        # Log the deletion
        log(
            log_type="info",
            message=f"User {get_jwt_identity()} deleted sector {settore}",
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={"endpoint": Sector.ENDPOINT_PATHS[1], "verb": "DELETE"},
        )

        # Return a success message
        return create_response(
            message={"outcome": "sector successfully deleted"},
            status_code=STATUS_CODES["no_content"],
        )

    @jwt_required()
    @check_authorization(allowed_roles=["admin"])
    def patch(self, settore) -> Response:
        """
        Update a sector.
        The request must include the sector name as a path variable.
        """

        # Validate request
        data = validate_json_request(request)
        if isinstance(data, str):
            return create_response(
                message={"error": data}, status_code=STATUS_CODES["bad_request"]
            )

        # Gather JSON data
        new_value: str = data.get("new_value")

        # Validate parameters
        if new_value is None or len(new_value) == 0 or not isinstance(new_value, str):
            return create_response(
                message={"error": "new_value parameter is required"},
                status_code=STATUS_CODES["bad_request"],
            )

        # Check if sector exists
        sector: Dict[str, Any] = fetchone_query(
            "SELECT * FROM settori WHERE settore = %s", (settore,)
        )
        if sector is None:
            return create_response(
                message={"outcome": "error, specified sector does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        # Update the sector
        execute_query(
            "UPDATE settori SET settore = %s WHERE settore = %s", (new_value, settore)
        )

        # Log the update
        log(
            log_type="info",
            message=f"User {get_jwt_identity()} updated sector {settore}",
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={"endpoint": Sector.ENDPOINT_PATHS[1], "verb": "PATCH"},
        )

        # Return a success message
        return create_response(
            message={"outcome": "sector successfully updated"},
            status_code=STATUS_CODES["ok"],
        )

    @jwt_required()
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def get(self) -> Response:
        """
        Get all sectors with pagination.
        The request can include limit and offset as query parameters.
        """

        # Gather URL parameters
        try:
            limit: int = (
                int(request.args.get("limit")) if request.args.get("limit") else 10
            )  # Default to 10
            offset: int = (
                int(request.args.get("offset")) if request.args.get("offset") else 0
            )  # Default to 0
        except (ValueError, TypeError) as ex:
            return create_response(
                message={"error": f"invalid limit or offset parameter: {ex}"},
                status_code=STATUS_CODES["bad_request"],
            )

        # This endpoint does not require filters as the table has only one column

        try:
            # Execute query
            sectors: List[Dict[str, Any]] = fetchall_query(
                "SELECT settore FROM settori LIMIT %s OFFSET %s", (limit, offset)
            )

            # Log the read
            log(
                log_type="info",
                message=f"User {get_jwt_identity()} read all sectors",
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                message_id="UserAction",
                structured_data={"endpoint": Sector.ENDPOINT_PATHS[0], "verb": "GET"},
            )

            # Return result
            return create_response(message=sectors, status_code=STATUS_CODES["ok"])
        except (ValueError, TypeError, IntegrityError) as err:

            # Log the error
            log(
                log_type="error",
                message=(
                    f"User {get_jwt_identity()} failed to "
                    f"read sectors with error: {str(err)}"
                ),
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                message_id="UserAction",
                structured_data={"endpoint": Sector.ENDPOINT_PATHS[0], "verb": "GET"},
            )

            # Return error response
            return create_response(
                message={"error": "internal server error"},
                status_code=STATUS_CODES["internal_error"],
            )

    @jwt_required()
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def options(self) -> Response:
        """
        Handle OPTIONS requests to provide allowed methods for the resource.
        This is useful for CORS preflight requests.
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


api.add_resource(Sector, *Sector.ENDPOINT_PATHS)
