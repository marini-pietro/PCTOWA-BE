"""
This module defines the Class resource for managing classes in the database.
It includes endpoints for creating, deleting, updating, and retrieving class data.
It also includes a fuzzy search endpoint for class names and one list endpoint.
"""

from re import match as re_match
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
    is_input_safe,
    handle_options_request,
    validate_json_request,
    check_column_existence,
    get_hateos_location_string,
)

# Define constants
BP_NAME = os_path_basename(__file__).replace("_bp.py", "")

# Create the blueprint and the API
class_bp = Blueprint(BP_NAME, __name__)
api = Api(class_bp)


class Class(Resource):
    """
    Class for managing classes in the database.
    It includes endpoints for creating, deleting, updating, and retrieving class data.
    """

    ENDPOINT_PATHS = [
        f"/{BP_NAME}",
        f"/{BP_NAME}/<int:id_>",
        f"/{BP_NAME}/<string:email_responsabile>",
    ]

    @jwt_required()
    @check_authorization(allowed_roles=["admin", "supertutor"])
    def post(self) -> Response:
        """
        Create a new class in the database.
        The request body must be a JSON object with application/json content type.
        """

        # Validate request
        data = validate_json_request(request)
        if isinstance(data, str):
            return create_response(
                message={"error": data}, status_code=STATUS_CODES["bad_request"]
            )

        # Gather parameters
        sigla: str = data.get("sigla")
        anno: str = data.get("anno")
        email_responsabile: str = data.get("email_responsabile")

        # Validate parameters
        missing_fields = [
            key
            for key, value in {
                "sigla": sigla,
                "anno": anno,
                "email_responsabile": email_responsabile,
            }.items()
            if value is None
        ]
        if missing_fields:
            return create_response(
                message={
                    "error": (
                        f'missing required fields: {", ".join(missing_fields)}, '
                        "check documentation for details"
                    )
                },
                status_code=STATUS_CODES["bad_request"],
            )
        if len(anno) != 5:
            return create_response(
                message={"error": "anno must be long 5 characters (e.g. 24-25)"},
                status_code=STATUS_CODES["bad_request"],
            )

        # Check if the year string is in the format 'xx-xx'
        if not re_match(r"^\d{4}-\d{4}$", anno):
            return create_response(
                message={"outcome": "invalid anno format"},
                status_code=STATUS_CODES["bad_request"],
            )

        # Check if the class variable is a number between 4 and 5 followed by two characters
        if not re_match(r"^([4-5]\d{0,1}[a-zA-Z]{2})$", sigla):
            return create_response(
                message={"outcome": "invalid sigla format"},
                status_code=STATUS_CODES["bad_request"],
            )

        # Check if the email string is a valid email format
        if not re_match(
            r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email_responsabile
        ):
            return create_response(
                message={"outcome": "invalid email format"},
                status_code=STATUS_CODES["bad_request"],
            )

        # Execute query to insert the class
        lastrowid: int = execute_query(
            "INSERT INTO classi (sigla, anno, email_responsabile) VALUES (%s, %s, %s)",
            (sigla, anno, email_responsabile),
        )

        # Log the creation of the class
        log(
            log_type="info",
            message=f"User {get_jwt_identity()} created class {lastrowid}",
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={"endpoint": {Class.ENDPOINT_PATHS[0]}, "verb": "POST"},
        )

        # Return a success message
        return create_response(
            message={
                "outcome": "class created",
                "location": get_hateos_location_string(bp_name=BP_NAME, id_=lastrowid),
            },
            status_code=STATUS_CODES["created"],
        )

    @jwt_required()
    @check_authorization(allowed_roles=["admin", "supertutor"])
    def delete(self, id_) -> Response:
        """
        Delete a class from the database.
        The class ID is passed as a path parameter.
        """

        # Check that class exists
        # Only fetch the province to check existence (could be any field)
        class_: Dict[str, Any] = fetchone_query(
            "SELECT sigla FROM classi WHERE id_classe = %s", (id_,)
        )
        if class_ is None:
            return create_response(
                message={"error": "specified class does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        # Delete the class
        execute_query("DELETE FROM classi WHERE id_classe = %s", (id_,))

        # Log the deletion of the class
        log(
            log_type="info",
            message=f"User {get_jwt_identity()} deleted class {id_}",
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={"endpoint": {Class.ENDPOINT_PATHS[1]}, "verb": "DELETE"},
        )

        # Return a success message
        return create_response(
            message={"outcome": "class deleted"}, status_code=STATUS_CODES["no_content"]
        )

    @jwt_required()
    @check_authorization(allowed_roles=["admin", "supertutor"])
    def patch(self, id_) -> Response:
        """
        Update a class in the database.
        The class ID is passed as a path parameter.
        """

        # Validate request
        data = validate_json_request(request)
        if isinstance(data, str):
            return create_response(
                message={"error": data}, status_code=STATUS_CODES["bad_request"]
            )

        # Check that class exists
        class_: Dict[str, Any] = fetchone_query(
            "SELECT sigla FROM classi WHERE id_classe = %s",
            (id_,),  # Only fetch the sigla to check existence (could be any field)
        )
        if class_ is None:
            return create_response(
                message={"outcome": "error, specified class does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        # Check that the specified fields actually exist in the database
        temp = check_column_existence(
            modifiable_columns=["sigla", "email_responsabile", "anno"],
            to_modify=list(data.keys()),
        )
        if isinstance(temp, str):
            return create_response(
                message={"outcome": temp},
                status_code=STATUS_CODES["bad_request"],
            )

        # Build the update query
        query, params = build_update_query_from_filters(
            data=data, table_name="classi", pk_column="id_classe", pk_value=id_
        )

        # Execute the update query
        execute_query(query, params)

        # Log the update of the class
        log(
            log_type="info",
            message=f"User {get_jwt_identity()} updated class {id_}",
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={"endpoint": {Class.ENDPOINT_PATHS[1]}, "verb": "PATCH"},
        )

        # Return a success message
        return create_response(
            message={"outcome": "class successfully updated"},
            status_code=STATUS_CODES["ok"],
        )

    @jwt_required()
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def get(self, email_responsabile) -> Response:
        """
        Get class data based on the email of the responsible teacher.
        """

        # Log the read
        log(
            log_type="info",
            message=(
                f"User {get_jwt_identity()} requested "
                f"to read class with email {email_responsabile}"
            ),
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={"endpoint": {Class.ENDPOINT_PATHS[2]}, "verb": "GET"},
        )

        # Check if user exists
        user: Dict[str, Any] = fetchone_query(
            "SELECT nome FROM utenti WHERE email_utente = %s",
            (
                email_responsabile
            ),  # Only fetch the name to check existence (could be any field)
        )
        if not user:
            return create_response(
                message={"outcome": "no user found with provided email"},
                status_code=STATUS_CODES["not_found"],
            )

        # Get class data
        classes_data: List[Dict[str, Any]] = fetchall_query(
            "SELECT sigla, email_responsabile, anno FROM classi WHERE email_responsabile = %s",
            (email_responsabile),
        )

        # Return the data
        return create_response(message=classes_data, status_code=STATUS_CODES["ok"])

    @jwt_required()
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def options(self) -> Response:
        """
        Handle OPTIONS request.
        This method is used to check which HTTP methods are allowed for this endpoint.
        """
        return handle_options_request(resource_class=self)


class ClassFuzzySearch(Resource):
    """
    Class for fuzzy search of class names in the database.
    """

    ENDPOINT_PATHS = [f"/{BP_NAME}/fsearch"]

    @jwt_required()
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def get(self) -> Response:
        """
        Execute fuzzy search for class names in database.
        """

        # Gather parameters
        input_str: str = request.args.get("fnome")
        if not input_str:
            return create_response(
                message={"error": "missing required field fnome"},
                status_code=STATUS_CODES["bad_request"],
            )
        if not isinstance(input_str, str):
            return create_response(
                message={"error": "fnome must be a string"},
                status_code=STATUS_CODES["bad_request"],
            )
        if "%" in input_str or "_" in input_str:
            return create_response(
                message={"error": "fnome cannot contain % or _ characters"},
                status_code=STATUS_CODES["bad_request"],
            )

        # Check for sql injection
        if not is_input_safe(input_str):
            return create_response(
                message={"error": "invalid input, suspected sql injection"},
                status_code=STATUS_CODES["bad_request"],
            )

        # Log the operation
        log(
            log_type="info",
            message=(
                f"User {get_jwt_identity()} requested fuzzy "
                f"search in classes with string {input_str}"
            ),
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={
                "endpoint": {ClassFuzzySearch.ENDPOINT_PATHS[0]},
                "verb": "GET",
            },
        )

        # Get the data
        data: List[Dict[str, Any]] = fetchall_query(
            query="SELECT sigla FROM classi WHERE sigla LIKE %s",
            params=(f"%{input_str}%",),
        )

        # Return the data
        return create_response(message=data, status_code=STATUS_CODES["ok"])

    @jwt_required()
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def options(self) -> Response:
        """
        Handle OPTIONS request.
        This method is used to check which HTTP methods are allowed for this endpoint.
        """
        return handle_options_request(resource_class=self)


class ClassList(Resource):
    """
    Class for listing all classes in the database.
    """

    ENDPOINT_PATHS = [f"/{BP_NAME}/list"]

    @jwt_required()
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def get(self) -> Response:
        """
        Get the names of all classes.
        """

        # Log the read operation
        log(
            log_type="info",
            message=f"User {get_jwt_identity()} read class list",
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={"endpoint": {ClassList.ENDPOINT_PATHS[0]}, "verb": "GET"},
        )

        # Get data
        class_names: List[Dict[str, Any]] = fetchall_query(
            "SELECT sigla FROM classi ORDER BY sigla DESC", ()
        )

        return create_response(message=class_names, status_code=STATUS_CODES["ok"])

    @jwt_required()
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def options(self) -> Response:
        """
        Handle OPTIONS request.
        This method is used to check which HTTP methods are allowed for this endpoint.
        """
        return handle_options_request(resource_class=self)


api.add_resource(Class, *Class.ENDPOINT_PATHS)
api.add_resource(ClassFuzzySearch, *ClassFuzzySearch.ENDPOINT_PATHS)
api.add_resource(ClassList, *ClassList.ENDPOINT_PATHS)
