"""
LegalForm Blueprint
This module defines a Flask blueprint for handling legal form related operations.
"""

from os.path import basename as os_path_basename
from typing import Any, Dict, List
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
legalform_bp = Blueprint(BP_NAME, __name__)
api = Api(legalform_bp)


# Marshmallow schema for LegalForm resource
class LegalFormSchema(ma.Schema):
    """
    Schema for validating and deserializing legal form data.
    """

    forma = fields.String(
        required=True,
        error_messages={
            "required": "forma is required.",
            "invalid": "forma must be a string.",
        },
    )


legalform_schema = LegalFormSchema()
legalform_schema_partial = LegalFormSchema(partial=True)


class LegalForm(Resource):
    """
    LegalForm class to handle legal form related operations.
    This class is a Flask-RESTful resource that provides endpoints
    to create, read, update, and delete legal forms.
    """

    ENDPOINT_PATHS = [f"/{BP_NAME}", f"/{BP_NAME}/<string:forma>"]

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor"])
    def post(self, identity) -> Response:
        """
        Create a new legal form.
        The request must contain a JSON body with application/json.
        """

        # Validate and deserialize input using Marshmallow
        try:
            data = legalform_schema.load(request.get_json())
        except ValidationError as err:
            return create_response(
                message={"errors": err.messages},
                status_code=STATUS_CODES["bad_request"],
            )

        forma: str = data["forma"]

        try:
            # Insert the legal form
            execute_query("INSERT INTO forma_giuridica (forma) VALUES (%s)", (forma,))
        except IntegrityError as ex:
            log(
                log_type="error",
                message=(
                    f"User {identity} tried to "
                    f"create legal form {forma} but it generated {ex}"
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
                    f"create legal form {forma} with error: {str(ex)}"
                ),
                structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
            )
            return create_response(
                message={"error": "internal server error"},
                status_code=STATUS_CODES["internal_error"],
            )

        # Log the legal form creation
        log(
            log_type="info",
            message=f"User {identity} created legal form {forma}",
            structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
        )

        # Return a success message
        return create_response(
            message={
                "outcome": "legal form successfully created",
                "location": get_hateos_location_string(bp_name=BP_NAME, id_=forma),
            },
            status_code=STATUS_CODES["created"],
        )

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor"])
    def delete(self, forma, identity) -> Response:
        """
        Delete a legal form.
        The legal form is passed as a path variable.
        """

        # Validate and deserialize input using Marshmallow (simulate for path param)
        try:
            legalform_schema.load({"forma": forma})
        except ValidationError as err:
            return create_response(
                message={"errors": err.messages},
                status_code=STATUS_CODES["bad_request"],
            )

        # Delete the legal form
        _, rows_affected = execute_query(
            "DELETE FROM forma_giuridica WHERE forma = %s", (forma,)
        )

        # Check if any rows were affected
        if rows_affected == 0:
            return create_response(
                message={"error": "specified legal form does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        # Log the deletion
        log(
            log_type="info",
            message=f"User {identity} deleted legal form {forma}",
            structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
        )

        # Return a success message
        return create_response(
            message={"outcome": "legal form successfully deleted"},
            status_code=STATUS_CODES["no_content"],
        )

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor"])
    def patch(self, forma, identity) -> Response:
        """
        Update a legal form.
        The legal form is passed as a path variable.
        """

        # Validate and deserialize input using Marshmallow (simulate for path param)
        try:
            legalform_schema.load({"forma": forma})
        except ValidationError as err:
            return create_response(
                message={"errors": err.messages},
                status_code=STATUS_CODES["bad_request"],
            )

        # Validate and deserialize input using Marshmallow (partial for new_value)
        try:
            data = legalform_schema_partial.load(request.get_json())
        except ValidationError as err:
            return create_response(
                message={"errors": err.messages},
                status_code=STATUS_CODES["bad_request"],
            )

        new_value: str = data.get("forma")
        if new_value is None or len(new_value) == 0:
            return create_response(
                message={"error": "invalid new legal form value"},
                status_code=STATUS_CODES["bad_request"],
            )

        # Check if legal form exists
        form: Dict[str, Any] = fetchone_query(
            "SELECT forma FROM forma_giuridica WHERE forma = %s", (forma,)
        )
        if form is None:
            return create_response(
                message={"outcome": "error, specified legal form does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        # Update the legal form
        execute_query(
            "UPDATE forma_giuridica SET forma = %s WHERE forma = %s", (new_value, forma)
        )

        # Log the update
        log(
            log_type="info",
            message=(f"User {identity} updated " f"legal form {forma} to {new_value}"),
            structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
        )

        # Return a success message
        return create_response(
            message={"outcome": "legal form successfully updated"},
            status_code=STATUS_CODES["ok"],
        )

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def get(self, identity) -> Response:
        """
        Get all legal forms.
        The results are paginated with limit and offset parameters.
        """
        # Gather query strings
        try:
            limit: int = int(request.args.get("limit", 10))
            offset: int = int(request.args.get("offset", 0))
            if limit < 0 or offset < 0:
                raise ValueError
        except ValueError:
            return create_response(
                message={"error": "limit and offset must be positive integers"},
                status_code=STATUS_CODES["bad_request"],
            )

        try:
            # Execute query
            forms: List[Dict[str, Any]] = fetchall_query(
                "SELECT forma FROM forma_giuridica LIMIT %s OFFSET %s",
                params=(limit, offset),
            )

            # Log the read
            log(
                log_type="info",
                message=f"User {identity} read all legal forms",
                structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
            )

            # Return the result
            return create_response(message=forms, status_code=STATUS_CODES["ok"])
        except (ValueError, TypeError, RuntimeError) as err:

            # Log the error
            log(
                log_type="error",
                message=(
                    f"User {identity} failed "
                    f"to read legal forms with error: {str(err)}"
                ),
                structured_data=f"[endpoint='{request.path} verb='{request.method}']",
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
        Handle OPTIONS request.
        This method returns the allowed HTTP methods for this endpoint.
        """
        return handle_options_request(resource_class=self)


api.add_resource(LegalForm, *LegalForm.ENDPOINT_PATHS)
