"""
This module defines the Address blueprint and its associated API endpoints.
"""

from os.path import basename as os_path_basename
from typing import List, Dict, Any

from flask import Blueprint, Response, request
from flask_restful import Api, Resource
from marshmallow import fields, ValidationError
from marshmallow.validate import Regexp
from api_server import ma

from config import (
    STATUS_CODES,
)
from .blueprints_utils import (
    build_update_query_from_filters,
    check_authorization,
    create_response,
    execute_query,
    fetchone_query,
    fetchall_query,
    handle_options_request,
    log,
    get_hateos_location_string,
    check_column_existence,
    jwt_validation_required,
)

# Define constants
BP_NAME = os_path_basename(__file__).replace("_bp.py", "")

# Create the blueprint and API
address_bp = Blueprint(BP_NAME, __name__)
api = Api(address_bp)


# Marshmallow schema for Address resource
class AddressSchema(ma.Schema):
    """
    Marshmallow schema for validating and deserializing address data.
    """

    stato = fields.String(
        required=True, error_messages={"required": "stato is required."}
    )
    provincia = fields.String(
        required=True, error_messages={"required": "provincia is required."}
    )
    comune = fields.String(
        required=True, error_messages={"required": "comune is required."}
    )
    cap = fields.String(
        required=True,
        validate=Regexp(r"^\d{5}$", error="CAP must be exactly 5 digits"),
        error_messages={
            "required": "cap is required.",
            "invalid": "cap must be a string of exactly 5 digits.",
        },
    )
    indirizzo = fields.String(
        required=True, error_messages={"required": "indirizzo is required."}
    )
    id_azienda = fields.Integer(
        required=True,
        error_messages={
            "required": "id_azienda is required.",
            "invalid": "id_azienda must be an integer.",
        },
    )


address_schema = AddressSchema()
address_schema_partial = AddressSchema(partial=True)


class Address(Resource):
    """
    Address class to handle API requests related to addresses.
    This class inherits from Resource and defines the endpoints for creating,
    deleting, updating, and retrieving addresses.
    """

    ENDPOINT_PATHS = [f"/{BP_NAME}", f"/{BP_NAME}/<int:id_>"]

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor"])
    def post(self, identity) -> Response:
        """
        Creates a new address in the database.
        This endpoint requires authentication and authorization.
        The request must contain a JSON in the body and application/json as Content-Type.
        """

        # Validate and deserialize input using Marshmallow
        try:
            data = address_schema.load(request.get_json())
        except ValidationError as err:
            return create_response(
                message={"errors": err.messages},
                status_code=STATUS_CODES["bad_request"],
            )

        # Check if id_azienda exists using EXISTS keyword
        company_exists: bool = fetchone_query(
            "SELECT EXISTS(SELECT 1 FROM aziende WHERE id_azienda = %s) AS ex",
            (data["id_azienda"],),
        )["ex"]
        if not company_exists:
            return create_response(
                message={"outcome": "error, specified company does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        # Insert the address
        lastrowid, _ = execute_query(
            "INSERT INTO indirizzi (stato, provincia, comune, cap, indirizzo, id_azienda) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (
                data["stato"],
                data["provincia"],
                data["comune"],
                data["cap"],
                data["indirizzo"],
                data["id_azienda"],
            ),
        )

        # Log the address creation
        log(
            log_type="info",
            message=f"User {identity} created address {lastrowid}",
            structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
        )

        return create_response(
            message={
                "outcome": "address successfully created",
                "location": get_hateos_location_string(bp_name=BP_NAME, id_=lastrowid),
            },
            status_code=STATUS_CODES["created"],
        )

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor"])
    def delete(self, id_, identity) -> Response:
        """
        Deletes an address from the database.
        This endpoint requires authentication and authorization.
        The request must contain the id parameter in the URI as a path variable.
        """

        # Delete the address
        _, rows_affected = execute_query(
            "DELETE FROM indirizzi WHERE id_indirizzo = %s", (id_,)
        )

        # Check if any rows were affected
        if rows_affected == 0:
            return create_response(
                message={"error": "specified address does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        # Log the deletion
        log(
            log_type="info",
            message=f"User {identity} deleted address {id_}",
            structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
        )

        return create_response(
            message=None,
            status_code=STATUS_CODES["no_content"],
        )

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor"])
    def patch(self, id_, identity) -> Response:
        """
        Updates an address in the database.
        This endpoint requires authentication and authorization.
        The request must contain the id parameter in the URI as a path variable.
        """

        # Validate and deserialize input using Marshmallow (partial update)
        try:
            data = address_schema_partial.load(request.get_json())
        except ValidationError as err:
            return create_response(
                message={"errors": err.messages},
                status_code=STATUS_CODES["bad_request"],
            )

        # Check if address exists using EXISTS keyword
        address_exists: bool = fetchone_query(
            "SELECT EXISTS(SELECT 1 FROM indirizzi WHERE id_indirizzo = %s) AS ex",
            (id_,),
        )["ex"]
        if not address_exists:
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
            message=f"User {identity} updated address {id_}",
            structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
        )

        return create_response(
            message=None,
            status_code=STATUS_CODES["no_content"],
        )

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def get(self, id_, identity) -> Response:
        """
        Retrieves all the addresses of a company from the database.
        This endpoint requires authentication and authorization.
        The request must contain the id parameter in the URI as a path variable.
        """

        # Gather parameters
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

        # Check that the company exists using EXISTS keyword
        company_exists: bool = fetchone_query(
            "SELECT EXISTS(SELECT 1 FROM aziende WHERE id_azienda = %s) AS ex",
            (id_,),
        )["ex"]
        if not company_exists:
            return create_response(
                message={"error": "specified company does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        try:
            # Execute query with limit and offset
            addresses: List[Dict[str, Any]] = fetchall_query(
                "SELECT id_indirizzo, stato, provincia, comune, cap, indirizzo "
                "FROM indirizzi WHERE id_azienda = %s LIMIT %s OFFSET %s",
                params=(id_, limit, offset),
            )

            # Log the read
            log(
                log_type="info",
                message=f"User {identity} read all the addresses of company with id: {id_}",
                structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
            )

            # Return the results
            return create_response(message=addresses, status_code=STATUS_CODES["ok"])
        except (
            ValueError,
            KeyError,
            RuntimeError,
        ) as err:  # Replace with specific exceptions

            # Log the error
            log(
                log_type="error",
                message=f"error while retrieving address data with id {id_}: {err}",
                structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
            )

            # Return a 500 error response
            return create_response(
                message={"error": "internal server error"},
                status_code=STATUS_CODES["internal_error"],
            )

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def options(self) -> Response:
        """
        Handles OPTIONS requests for the Address resource.
        This method is used to determine the allowed HTTP methods for this resource.
        It returns a 200 OK response with the allowed methods in the Allow header.
        """

        return handle_options_request(resource_class=self)


api.add_resource(Address, *Address.ENDPOINT_PATHS)
