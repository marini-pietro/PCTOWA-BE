"""
Blueprint for managing sectors in the database.
This module provides a RESTful API for creating, deleting, updating, and retrieving sectors.
It also includes authorization checks and logging for each operation.
"""

from os.path import basename as os_path_basename
from typing import Dict, List, Any
from flask import Blueprint, request, Response
from flask_restful import Api, Resource
from marshmallow import fields, ValidationError
from mysql.connector import IntegrityError
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
    handle_options_request,
    get_hateos_location_string,
    jwt_validation_required,
)

# Define constants
BP_NAME = os_path_basename(__file__).replace("_bp.py", "")

# Create the blueprint and API
sector_bp = Blueprint(BP_NAME, __name__)
api = Api(sector_bp)


# Marshmallow schema for Sector resource
class SectorSchema(ma.Schema):
    """
    Schema for validating and deserializing sector data.
    """

    settore = fields.String(
        required=True,
        error_messages={
            "required": "settore is required.",
            "invalid": "settore must be a string.",
        },
    )


sector_schema = SectorSchema()
sector_schema_partial = SectorSchema(partial=True)


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

    ENDPOINT_PATHS = [f"/{BP_NAME}", f"/{BP_NAME}/<string:settore>"]

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin"])
    def post(self, identity) -> Response:
        """
        Create a new sector.
        The request body must be a JSON object with application/json content type.
        """

        # Validate and deserialize input using Marshmallow
        try:
            data = sector_schema.load(request.get_json())
        except ValidationError as err:
            return create_response(
                message={"errors": err.messages},
                status_code=STATUS_CODES["bad_request"],
            )

        settore: str = data["settore"]

        if len(settore) > 255:
            return create_response(
                message={"error": "settore parameter is too long"},
                status_code=STATUS_CODES["bad_request"],
            )

        try:
            # Insert the sector
            lastrowid, _ = execute_query(
                "INSERT INTO settori (settore) VALUES (%s)", (settore,)
            )
        except IntegrityError as ex:
            log(
                log_type="error",
                message=(
                    f"User {identity} tried "
                    f"to create sector {settore} but it generated {ex}"
                ),
                structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
            )
            return create_response(
                message={"error": "conflict error"},
                status_code=STATUS_CODES["conflict"],
            )
        except (ValueError, TypeError) as ex:
            log(
                log_type="error",
                message=(
                    f"User {identity} failed to "
                    f"create sector {settore} with error: {str(ex)}"
                ),
                structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
            )
            return create_response(
                message={"error": "internal server error"},
                status_code=STATUS_CODES["internal_error"],
            )

        # Log the sector creation
        log(
            log_type="info",
            message=f"User {identity} created sector {settore}",
            structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
        )

        # Return a success message
        return create_response(
            message={
                "outcome": "sector successfully created",
                "location": get_hateos_location_string(bp_name=BP_NAME, id_=lastrowid),
            },
            status_code=STATUS_CODES["created"],
        )

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin"])
    def delete(self, settore, identity) -> Response:
        """
        Delete a sector.
        The request must include the sector name as a path variable.
        """

        # Validate and deserialize input using Marshmallow (simulate for path param)
        try:
            sector_schema.load({"settore": settore})
        except ValidationError as err:
            return create_response(
                message={"errors": err.messages},
                status_code=STATUS_CODES["bad_request"],
            )

        if len(settore) > 255:
            return create_response(
                message={"error": "settore parameter is too long"},
                status_code=STATUS_CODES["bad_request"],
            )

        # Delete the sector
        _, rows_affected = execute_query(
            "DELETE FROM settori WHERE settore = %s", (settore,)
        )

        # Check if any rows were affected
        if rows_affected == 0:
            return create_response(
                message={"error": "specified sector does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        # Log the deletion
        log(
            log_type="info",
            message=f"User {identity} deleted sector {settore}",
            structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
        )

        # Return a success message
        return create_response(
            message={"outcome": "sector successfully deleted"},
            status_code=STATUS_CODES["no_content"],
        )

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin"])
    def patch(self, settore, identity) -> Response:
        """
        Update a sector.
        The request must include the sector name as a path variable.
        """

        # Validate and deserialize input using Marshmallow (simulate for path param)
        try:
            sector_schema.load({"settore": settore})
        except ValidationError as err:
            return create_response(
                message={"errors": err.messages},
                status_code=STATUS_CODES["bad_request"],
            )

        # Validate and deserialize input using Marshmallow (partial for new_value)
        try:
            data = sector_schema_partial.load(request.get_json())
        except ValidationError as err:
            return create_response(
                message={"errors": err.messages},
                status_code=STATUS_CODES["bad_request"],
            )

        new_value: str = data.get("settore")
        if new_value is None or len(new_value) == 0:
            return create_response(
                message={"error": "settore parameter is required"},
                status_code=STATUS_CODES["bad_request"],
            )
        if len(new_value) > 255:
            return create_response(
                message={"error": "settore parameter is too long"},
                status_code=STATUS_CODES["bad_request"],
            )

        # Check if sector exists
        sector: Dict[str, Any] = fetchone_query(
            "SELECT settore FROM settori WHERE settore = %s", (settore,)
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
            message=f"User {identity} updated sector {settore}",
            structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
        )

        # Return a success message
        return create_response(
            message={"outcome": "sector successfully updated"},
            status_code=STATUS_CODES["ok"],
        )

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def get(self, identity) -> Response:
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

        try:
            # Execute query
            sectors: List[Dict[str, Any]] = fetchall_query(
                "SELECT settore FROM settori LIMIT %s OFFSET %s", (limit, offset)
            )

            # Log the read
            log(
                log_type="info",
                message=f"User {identity} read all sectors",
                structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
            )

            # Return result
            return create_response(message=sectors, status_code=STATUS_CODES["ok"])
        except (ValueError, TypeError, IntegrityError) as err:

            # Log the error
            log(
                log_type="error",
                message=(
                    f"User {identity} failed to " f"read sectors with error: {str(err)}"
                ),
                structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
            )

            # Return error response
            return create_response(
                message={"error": "internal server error"},
                status_code=STATUS_CODES["internal_error"],
            )

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def options(self) -> Response:
        """
        Handle OPTIONS requests to provide allowed methods for the resource.
        This is useful for CORS preflight requests.
        """

        return handle_options_request(resource_class=self)


api.add_resource(Sector, *Sector.ENDPOINT_PATHS)
