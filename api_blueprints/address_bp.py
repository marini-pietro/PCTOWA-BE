"""
This module defines the Address blueprint and its associated API endpoints.
"""

from os.path import basename as os_path_basename
from typing import Any, Dict

from flask import Blueprint, Response, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Api, Resource

from config import (
    API_SERVER_HOST,
    API_SERVER_NAME_IN_LOG,
    STATUS_CODES,
)
from .blueprints_utils import (
    build_update_query_from_filters,
    check_authorization,
    create_response,
    execute_query,
    fetchone_query,
    handle_options_request,
    log,
    validate_json_request,
    get_hateos_location_string,
    check_column_existence,
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

    ENDPOINT_PATHS = [f"/{BP_NAME}", f"/{BP_NAME}/<int:id_>"]

    @jwt_required()
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

        # Validate parameters and performing casting if necessary
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
            "SELECT fax FROM aziende WHERE id_azienda = %s",
            (id_azienda,),  # Only fetch the fax to check existence (could be any field)
        )
        if company is None:
            return create_response(
                message={"outcome": "error, specified company does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        # Insert the address
        lastrowid = execute_query(
            "INSERT INTO indirizzi (stato, provincia, comune, cap, indirizzo, id_azienda) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (stato, provincia, comune, cap, indirizzo, id_azienda),
        )

        # Log the address creation
        log(
            log_type="info",
            message=f"User {get_jwt_identity()} created address {lastrowid}",
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={"endpoint": Address.ENDPOINT_PATHS[0], "verb": "POST"},
        )

        return create_response(
            message={
                "outcome": "address successfully created",
                "location": get_hateos_location_string(bp_name=BP_NAME, id_=lastrowid),
            },
            status_code=STATUS_CODES["created"],
        )

    @jwt_required()
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
            message=f"User {get_jwt_identity()} deleted address {id_}",
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={"endpoint": Address.ENDPOINT_PATHS[1], "verb": "DELETE"},
        )

        return create_response(
            message={"outcome": "address successfully deleted"},
            status_code=STATUS_CODES["no_content"],
        )

    @jwt_required()
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
            "SELECT stato FROM indirizzi WHERE id_indirizzo = %s",
            (id_,),  # Only fetch the state to check existence (could be any field)
        )
        if address is None:
            return create_response(
                message={"outcome": "error, specified address does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        # Check that the specified fields actually exist in the database
        temp = check_column_existence(
            modifiable_columns=[
                "stato",
                "provincia",
                "comune",
                "cap",
                "indirizzo",
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
            data=data, table_name="indirizzi", pk_column="id_indirizzo", pk_value=id_
        )

        # Update the address
        execute_query(query=query, params=params)

        # Log the update
        log(
            log_type="info",
            message=f"User {get_jwt_identity()} updated address {id_}",
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={"endpoint": Address.ENDPOINT_PATHS[1], "verb": "PATCH"},
        )

        # Return a success message
        return create_response(
            message={"outcome": f"address {id_} successfully updated"},
            status_code=STATUS_CODES["ok"],
        )

    @jwt_required()
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def get(self, id_) -> Response:
        """
        Retrieves an address from the database.
        This endpoint requires authentication and authorization.
        The request must contain the id parameter in the URI as a path variable.
        """

        # Check if address exists
        address = fetchone_query(
            "SELECT stato FROM indirizzi WHERE id_indirizzo = %s",
            (id_,),  # Only fetch the state to check existence (could be any field)
        )
        if address is None:
            return create_response(
                message={"error": "specified address does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        try:
            # Execute query
            address = fetchone_query(
                "SELECT stato, provincia, comune, cap, indirizzo, id_azienda FROM indirizzi WHERE id_indirizzo = %s",
                params=(id_,),
            )

            # Log the read
            log(
                log_type="info",
                message=f"User {get_jwt_identity()} read addres {id_}",
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                message_id="UserAction",
                structured_data={"endpoint": Address.ENDPOINT_PATHS[1], "verb": "GET"},
            )

            # Return the results
            return create_response(message=address, status_code=STATUS_CODES["ok"])
        except (
            ValueError,
            KeyError,
            RuntimeError,
        ) as err:  # Replace with specific exceptions

            # Log the error
            log(
                log_type="error",
                message=f"error while retrieving address data with id {id_}: {err}",
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                message_id="UserAction",
                structured_data={
                    "endpoint": Address.ENDPOINT_PATHS[1],
                    "verb": "GET",
                },
            )

            # Return a 500 error response
            return create_response(
                message={"error": "interal server error"},
                status_code=STATUS_CODES["internal_error"],
            )

    @jwt_required()
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def options(self) -> Response:
        """
        Handles OPTIONS requests for the Address resource.
        This method is used to determine the allowed HTTP methods for this resource.
        It returns a 200 OK response with the allowed methods in the Allow header.
        """

        return handle_options_request(resource_class=self)


api.add_resource(Address, *Address.ENDPOINT_PATHS)
