"""
LegalForm Blueprint
This module defines a Flask blueprint for handling legal form related operations.
"""

from os.path import basename as os_path_basename
from typing import Any, Dict, List
from config import (
    API_SERVER_HOST,
    API_SERVER_PORT,
    API_SERVER_NAME_IN_LOG,
    STATUS_CODES,
)

from flask import Blueprint, request, Response
from flask_restful import Api, Resource
from flask_jwt_extended import get_jwt_identity
from mysql.connector import IntegrityError

from .blueprints_utils import (
    check_authorization,
    fetchone_query,
    fetchall_query,
    execute_query,
    log,
    jwt_required_endpoint,
    create_response,
    get_class_http_verbs,
    validate_json_request,
)

# Define constants
BP_NAME = os_path_basename(__file__).replace("_bp.py", "")

# Create the blueprint and API
legalform_bp = Blueprint(BP_NAME, __name__)
api = Api(legalform_bp)


class LegalForm(Resource):
    """
    LegalForm class to handle legal form related operations.
    This class is a Flask-RESTful resource that provides endpoints to create, read, update, and delete legal forms.
    """

    ENDPOINT_PATHS = [f"/{BP_NAME}", f"{BP_NAME}/<string:forma>"]

    @jwt_required_endpoint
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor"])
    def post(self) -> Response:
        """
        Create a new legal form.
        The request must contain a JSON body with application/json.
        """

        # Validate request
        data = validate_json_request(request)
        if isinstance(data, str):
            return create_response(
                message={"error": data}, status_code=STATUS_CODES["bad_request"]
            )

        # Gather parameters
        forma: str = data.get("forma")

        # Validate parameters
        if forma is None or not isinstance(forma, str) or len(forma) == 0:
            return create_response(
                message={"error": "Invalid legal form value"},
                status_code=STATUS_CODES["bad_request"],
            )

        try:
            # Insert the legal form
            execute_query("INSERT INTO formaGiuridica (forma) VALUES (%s)", (forma,))
        except IntegrityError as ex:
            log(
                log_type="error",
                message=f'User {get_jwt_identity().get("email")} tried to create legal form {forma} but it generated {ex}',
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                message_id="UserAction",
                structured_data={
                    "endpoint": {LegalForm.ENDPOINT_PATHS[0]},
                    "verb": "POST",
                },
            )
            return create_response(
                message={"error": "conflict error"},
                status_code=STATUS_CODES["conflict"],
            )
        except Exception as ex:
            log(
                log_type="error",
                message=f'User {get_jwt_identity().get("email")} failed to create legal form {forma} with error: {str(ex)}',
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                message_id="UserAction",
                structured_data={
                    "endpoint": {LegalForm.ENDPOINT_PATHS[0]},
                    "verb": "POST",
                },
            )
            return create_response(
                message={"error": "internal server error"},
                status_code=STATUS_CODES["internal_error"],
            )

        # Log the legal form creation
        log(
            log_type="info",
            message=f'User {get_jwt_identity().get("email")} created legal form {forma}',
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={"endpoint": {LegalForm.ENDPOINT_PATHS[0]}, "verb": "POST"},
        )

        # Return a success message
        return create_response(
            message={
                "outcome": "legal form successfully created",
                "location": f"http://{API_SERVER_HOST}:{API_SERVER_PORT}/api/{BP_NAME}/{forma}",
            },
            status_code=STATUS_CODES["created"],
        )

    @jwt_required_endpoint
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor"])
    def delete(self, forma) -> Response:
        """
        Delete a legal form.
        The legal form is passed as a path variable.
        """

        # Check that the legal form exists
        form: Dict[str, Any] = fetchone_query(
            "SELECT forma FROM formaGiuridica WHERE forma = %s", (forma,)
        )
        if form is None:
            return create_response(
                message={"error": "specified legal form does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        # Delete the legal form
        execute_query("DELETE FROM formaGiuridica WHERE forma = %s", (forma,))

        # Log the deletion
        log(
            log_type="info",
            message=f'User {get_jwt_identity().get("email")} deleted legal form {forma}',
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={
                "endpoint": {LegalForm.ENDPOINT_PATHS[1]},
                "verb": "DELETE",
            },
        )

        # Return a success message
        return create_response(
            message={"outcome": "legal form successfully deleted"},
            status_code=STATUS_CODES["no_content"],
        )

    @jwt_required_endpoint
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor"])
    def patch(self, forma) -> Response:
        """
        Update a legal form.
        The legal form is passed as a path variable.
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
        if new_value is None or not isinstance(new_value, str) or len(new_value) == 0:
            return create_response(
                message={"error": "Invalid legal form value"},
                status_code=STATUS_CODES["bad_request"],
            )

        # Check if legal form exists
        form: Dict[str, Any] = fetchone_query(
            "SELECT * FROM formaGiuridica WHERE forma = %s", (forma,)
        )
        if form is None:
            return create_response(
                message={"outcome": "error, specified legal form does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        # Update the legal form
        execute_query(
            "UPDATE formaGiuridica SET forma = %s WHERE forma = %s", (new_value, forma)
        )

        # Log the update
        log(
            log_type="info",
            message=f'User {get_jwt_identity().get("email")} updated legal form {forma} to {new_value}',
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={
                "endpoint": {LegalForm.ENDPOINT_PATHS[1]},
                "verb": "PATCH",
            },
        )

        # Return a success message
        return create_response(
            message={"outcome": "legal form successfully updated"},
            status_code=STATUS_CODES["ok"],
        )

    @jwt_required_endpoint
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def get(self) -> Response:
        """
        Get all legal forms.
        The results are paginated with limit and offset parameters.
        """
        # Gather URL parameters
        try:
            limit: int = (
                int(request.args.get("limit")) if request.args.get("limit") else 10
            )  # Default limit is 10
            offset: int = (
                int(request.args.get("offset")) if request.args.get("offset") else 0
            )  # Default offset is 0
        except (ValueError, TypeError) as ex:
            return create_response(
                message={"error": f"invalid limit or offset parameter: {ex}"},
                status_code=STATUS_CODES["bad_request"],
            )

        # This endpoint does not require filters as the table has only one column

        try:
            # Execute query
            forms: List[Dict[str, Any]] = fetchall_query(
                "SELECT forma FROM formaGiuridica LIMIT %s OFFSET %s",
                params=(limit, offset),
            )

            # Log the read
            log(
                log_type="info",
                message=f'User {get_jwt_identity().get("email")} read all legal forms',
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                message_id="UserAction",
                structured_data={
                    "endpoint": {LegalForm.ENDPOINT_PATHS[0]},
                    "verb": "GET",
                },
            )

            # Return the result
            return create_response(message=forms, status_code=STATUS_CODES["ok"])
        except Exception as err:
            return create_response(
                message={"error": str(err)}, status_code=STATUS_CODES["internal_error"]
            )

    @jwt_required_endpoint
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def options(self) -> Response:
        """
        Handle OPTIONS request.
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


api.add_resource(LegalForm, *LegalForm.ENDPOINT_PATHS)
