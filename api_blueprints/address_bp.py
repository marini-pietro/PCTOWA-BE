"""
This module defines the Address blueprint and its associated API endpoints.
"""

from os.path import basename as os_path_basename
from typing import Any, Dict

from flask import Blueprint, Response, request
from flask_jwt_extended import get_jwt_identity
from flask_restful import Api, Resource

from config import (
    API_SERVER_HOST,
    API_SERVER_PORT,
    API_SERVER_NAME_IN_LOG,
    STATUS_CODES,
)
from .blueprints_utils import (
    build_select_query_from_filters,
    build_update_query_from_filters,
    check_authorization,
    create_response,
    execute_query,
    fetchall_query,
    fetchone_query,
    get_class_http_verbs,
    jwt_required_endpoint,
    log,
    validate_json_request,
)

# Define constants
BP_NAME = os_path_basename(__file__).replace("_bp.py", "")

# Create the blueprint and API
address_bp = Blueprint(BP_NAME, __name__)
api = Api(address_bp)


class Address(Resource):
    """
    Address class to handle API requests related to addresses.
    This class inherits from Resource and defines the endpoints for creating,
    deleting, updating, and retrieving addresses.
    """

    ENDPOINT_PATHS = [f"/{BP_NAME}", f"/{BP_NAME}/<int:id>"]

    @jwt_required_endpoint
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor"])
    def post(self) -> Response:
        """
        Creates a new address in the database.
        This endpoint requires authentication and authorization.
        The request must contain a JSON in the body and application/json as Content-Type.
        """

        # Validate request
        data = validate_json_request(request)
        if isinstance(data, str):
            return create_response(
                message={"error": data}, status_code=STATUS_CODES["bad_request"]
            )

        # Gather parameters
        stato = data.get("stato")
        provincia = data.get("provincia")
        comune = data.get("comune")
        cap = data.get("cap")
        indirizzo: str = data.get("indirizzo")
        id_azienda: int = data.get("id_azienda")

        # Validate parameters
        if id_azienda is not None:
            try:
                id_azienda = int(id_azienda)
            except ValueError:
                return create_response(
                    message={"error": "invalid id_azienda parameter"},
                    status_code=STATUS_CODES["bad_request"],
                )

        # Check if id_azienda exists
        company = fetchone_query(
            "SELECT * FROM aziende WHERE id_azienda = %s", (id_azienda,)
        )
        if company is None:
            return create_response(
                message={"outcome": "error, specified company does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        # Insert the address
        lastrowid = execute_query(
            "INSERT INTO indirizzi (stato, provincia, comune, cap, indirizzo, id_azienda) VALUES (%s, %s, %s, %s, %s, %s)",
            (stato, provincia, comune, cap, indirizzo, id_azienda),
        )

        # Log the address creation
        log(
            log_type="info",
            message=f'User {get_jwt_identity().get("email")} created address {lastrowid}',
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={"endpoint": Address.ENDPOINT_PATHS[0], "verb": "POST"},
        )

        return create_response(
            message={
                "outcome": "address successfully created",
                "location": f"http://{API_SERVER_HOST}:{API_SERVER_PORT}/api/{BP_NAME}/{lastrowid}",
            },
            status_code=STATUS_CODES["created"],
        )

    @jwt_required_endpoint
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor"])
    def delete(self, id_) -> Response:
        """
        Deletes an address from the database.
        This endpoint requires authentication and authorization.
        The request must contain the id parameter in the URI as a path variable.
        """

        # Check that specified resource exists
        address: Dict[str, Any] = fetchone_query(
            "SELECT provincia FROM indirizzi WHERE id_indirizzo = %s", (id_,)
        )  # Only fetch the province to check existence (could be any field)
        if address is None:  # If the address does not exist, return a 404 error
            return create_response(
                message={"error": "specified address does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        # Delete the address
        execute_query("DELETE FROM indirizzi WHERE id_indirizzo = %s", (id_,))

        # Log the deletion
        log(
            log_type="info",
            message=f'User {get_jwt_identity().get("email")} deleted address {id_}',
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={"endpoint": Address.ENDPOINT_PATHS[1], "verb": "DELETE"}
        )

        return create_response(
            message={"outcome": "address successfully deleted"},
            status_code=STATUS_CODES["no_content"],
        )

    @jwt_required_endpoint
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor"])
    def patch(self, id_) -> Response:
        """
        Updates an address in the database.
        This endpoint requires authentication and authorization.
        The request must contain the id parameter in the URI as a path variable.
        """

        # Validate request
        data = validate_json_request(request)
        if isinstance(data, str):
            return create_response(
                message={"error": data}, status_code=STATUS_CODES["bad_request"]
            )

        # Check if address exists
        address = fetchone_query(
            "SELECT * FROM indirizzi WHERE id_indirizzo = %s", (id_,)
        )
        if address is None:
            return create_response(
                message={"outcome": "error, specified address does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        # Check that the specified fields actually exist in the database
        modifiable_columns: set = {
            "stato",
            "provincia",
            "comune",
            "cap",
            "indirizzo",
            "id_azienda",
        }
        to_modify: list[str] = list(data.keys())
        error_columns = [
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
            data=data, table_name="indirizzi", id_column="id_indirizzo", id_value=id_
        )

        # Update the address
        execute_query(query=query, params=params)

        # Log the update
        log(
            log_type="info",
            message=f'User {get_jwt_identity().get("email")} updated address {id_}',
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={"endpoint": Address.ENDPOINT_PATHS[1], "verb": "PATCH"}
        )

        # Return a success message
        return create_response(
            message={"outcome": f"address {id_} successfully updated"},
            status_code=STATUS_CODES["ok"],
        )

    @jwt_required_endpoint
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def get(self, id_) -> Response:
        """
        Retrieves an address from the database.
        This endpoint requires authentication and authorization.
        The request must contain the id parameter in the URI as a path variable.
        """
        # Gather parameters
        try:
            limit = int(
                request.args.get("limit", 10)
            )  # Default limit to 10 if not provided
            offset = int(
                request.args.get("offset", 0)
            )  # Default offset to 0 if not provided
        except ValueError:
            return create_response(
                message={"error": "limit and offset must be integers"},
                status_code=STATUS_CODES["bad_request"],
            )
        try:
            id_azienda = int(request.args.get("id_azienda"))
        except ValueError:
            return create_response(
                message={"error": "invalid id_azienda parameter"},
                status_code=STATUS_CODES["bad_request"],
            )

        # Build filter data dictionary
        data = {
            key: request.args.get(key)
            for key in [
                "id_indirizzo",
                "stato",
                "provincia",
                "comune",
                "cap",
                "indirizzo",
            ]
        }
        if id_azienda is not None:
            data["id_azienda"] = id_azienda

        # If 'id' is provided, add it to the filter
        if id_ is not None:
            data["id_indirizzo"] = id_

        try:
            # Build the query
            query, params = build_select_query_from_filters(
                data=data, table_name="indirizzi", limit=limit, offset=offset
            )

            # Execute query
            addresses = fetchall_query(query, params)

            # Get the ids to log
            ids = [address["id_indirizzo"] for address in addresses]

            # Log the read
            log(
                log_type="info",
                message=f'User {get_jwt_identity().get("email")} read address {ids}',
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                message_id="UserAction",
                structured_data={"endpoint": Address.ENDPOINT_PATHS[1], "verb": 'GET'},
            )

            # Return the results
            return create_response(message=addresses, status_code=STATUS_CODES["ok"])
        except Exception as err:
            return create_response(
                message={"error": str(err)}, status_code=STATUS_CODES["internal_error"]
            )

    @jwt_required_endpoint
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def options(self) -> Response:
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


api.add_resource(Address, *Address.ENDPOINT_PATHS)
