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
from marshmallow import fields, ValidationError
from marshmallow.validate import Regexp
from api_server import ma

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
    jwt_validation_required,
)

# Define constants
BP_NAME = os_path_basename(__file__).replace("_bp.py", "")

# Create the blueprint and the API
class_bp = Blueprint(BP_NAME, __name__)
api = Api(class_bp)


# Marshmallow schema for Class resource
class ClassSchema(ma.Schema):
    sigla = fields.String(
        required=True,
        validate=Regexp(
            r"^[1-5][A-Za-z]{2}$",
            error="sigla must be a digit from 1 to 5 followed by two letters (e.g. 4AI, 5BI)",
        ),
        error_messages={"required": "sigla is required."},
    )
    anno = fields.String(
        required=True,
        validate=Regexp(
            r"^\d{2}-\d{2}$", error="anno must be in the format xx-xx with digits"
        ),
        error_messages={"required": "anno is required."},
    )
    email_responsabile = fields.Email(
        required=True,
        error_messages={
            "required": "email_responsabile is required.",
            "invalid": "email_responsabile must be a valid email address.",
        },
    )


class_schema = ClassSchema()
class_schema_partial = ClassSchema(partial=True)


class Class(Resource):
    """
    Class for managing classes in the database.
    It includes endpoints for creating, deleting, updating, and retrieving class data.
    """

    ENDPOINT_PATHS = [
        f"/{BP_NAME}",
        f"/{BP_NAME}/<int:id_>",
        f"/{BP_NAME}/<string:class_year>",
    ]

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor"])
    def post(self, identity) -> Response:
        """
        Create a new class in the database.
        The request body must be a JSON object with application/json content type.
        """

        # Validate and deserialize input using Marshmallow
        try:
            data = class_schema.load(request.get_json())
        except ValidationError as err:
            return create_response(
                message={"errors": err.messages},
                status_code=STATUS_CODES["bad_request"],
            )

        sigla: str = data["sigla"].upper()
        anno: str = data["anno"]
        email_responsabile: str = data["email_responsabile"]

        # Execute query to insert the class
        lastrowid, _ = execute_query(
            "INSERT INTO classi (sigla, anno, email_responsabile) VALUES (%s, %s, %s)",
            (sigla, anno, email_responsabile),
        )

        # Log the creation of the class
        log(
            log_type="info",
            message=f"User {identity} created class {lastrowid}",
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data=f"[endpoint='{request.path} verb='{request.method}']",
        )

        # Return a success message
        return create_response(
            message={
                "outcome": "class created",
                "location": get_hateos_location_string(bp_name=BP_NAME, id_=lastrowid),
            },
            status_code=STATUS_CODES["created"],
        )

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor"])
    def delete(self, id_, identity) -> Response:
        """
        Delete a class from the database.
        The class ID is passed as a path parameter.
        """

        # Delete the class
        _, rows_affected = execute_query(
            "DELETE FROM classi WHERE id_classe = %s", (id_,)
        )

        if rows_affected == 0:
            return create_response(
                message={"error": "specified class does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        # Log the deletion of the class
        log(
            log_type="info",
            message=f"User {identity} deleted class {id_}",
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
        )

        # Return a success message
        return create_response(
            message={"outcome": "class deleted"}, status_code=STATUS_CODES["no_content"]
        )

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor"])
    def patch(self, id_, identity) -> Response:
        """
        Update a class in the database.
        The class ID is passed as a path parameter.
        """

        # Validate and deserialize input using Marshmallow (partial update)
        try:
            data = class_schema_partial.load(request.get_json())
        except ValidationError as err:
            return create_response(
                message={"errors": err.messages},
                status_code=STATUS_CODES["bad_request"],
            )

        # Check that class exists using EXISTS
        class_exists = fetchone_query(
            "SELECT EXISTS(SELECT 1 FROM classi WHERE id_classe = %s) AS class_exists",
            (id_,),
        )
        if not class_exists["class_exists"]:
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
            message=f"User {identity} updated class {id_}",
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
        )

        # Return a success message
        return create_response(
            message={"outcome": "class successfully updated"},
            status_code=STATUS_CODES["ok"],
        )

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def get(self, class_year, identity) -> Response:
        """
        Get all the students that belong to a class in a given year (e.g. 5BI 24-25).
        """

        # Log the read
        log(
            log_type="info",
            message=(
                f"User {identity} requested "
                f"to read classes with string {class_year}"
            ),
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
        )

        # Check if class_year is valid
        try:
            class_, year = class_year.split(" ")
            class_ = class_.upper()
        except ValueError:
            return create_response(
                message={
                    "error": "class_year must be in the format '<class> <year>' "
                    "(e.g., '5BI 24-25')"
                },
                status_code=STATUS_CODES["bad_request"],
            )

        # Validate class and year
        if not re_match(r"^[1-5][A-Za-z]{2}$", class_):
            return create_response(
                message={
                    "error": "class must be a digit from 1 to 5 followed by two letters (e.g. 4AI, 5BI)"
                },
                status_code=STATUS_CODES["bad_request"],
            )
        if not re_match(r"^\d{2}-\d{2}$", year):
            return create_response(
                message={"error": "year must be in the format xx-xx with digits"},
                status_code=STATUS_CODES["bad_request"],
            )

        # Get class data
        id_class: Dict[str, Any] = fetchone_query(
            "SELECT id_classe FROM classi WHERE sigla = %s AND anno = %s",
            (class_, year),
        )["id_classe"]

        # Check if class exists
        if id_class is None:
            return create_response(
                message={"error": "class not found"},
                status_code=STATUS_CODES["not_found"],
            )

        # Get students in the class
        students: List[Dict[str, Any]] = fetchall_query(
            "SELECT matricola, nome, cognome, comune "
            "FROM studenti "
            "JOIN classi ON studenti.id_classe = classi.id_classe "
            "WHERE classi.sigla = %s AND classi.anno = %s",
            (class_, year),
        )

        # Return the data
        return create_response(message=students, status_code=STATUS_CODES["ok"])

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def options(self) -> Response:
        """
        Handle OPTIONS request.
        This method is used to check which HTTP methods are allowed for this endpoint.
        """
        return handle_options_request(resource_class=self)


class ClassFromResponsible(Resource):
    """
    Class for managing classes based on the email of the responsible teacher.
    It includes endpoints for retrieving class data based on the email of the responsible teacher.
    """

    ENDPOINT_PATHS = [
        f"/{BP_NAME}",
        f"/{BP_NAME}/<string:email_responsabile>",
    ]

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def get(self, email_responsabile, identity) -> Response:
        """
        Get class data based on the email of the responsible teacher.
        """

        # Log the read
        log(
            log_type="info",
            message=(
                f"User {identity} requested "
                f"to read class with email {email_responsabile}"
            ),
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
        )

        # Check if user exists using EXISTS
        user_exists = fetchone_query(
            "SELECT EXISTS(SELECT 1 FROM utenti WHERE email_utente = %s) AS user_exists",
            (email_responsabile,),
        )
        if not user_exists["user_exists"]:
            return create_response(
                message={"outcome": "no user found with provided email"},
                status_code=STATUS_CODES["not_found"],
            )

        # Get class data
        classes_data: List[Dict[str, Any]] = fetchall_query(
            "SELECT sigla, email_responsabile, anno FROM classi WHERE email_responsabile = %s",
            (email_responsabile,),
        )

        # Return the data
        return create_response(message=classes_data, status_code=STATUS_CODES["ok"])

    @jwt_validation_required
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

    ENDPOINT_PATHS = [f"/{BP_NAME}/fsearch/<string:input_str>"]

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def get(self, identity, input_str="") -> Response:
        """
        Execute fuzzy search for class names in database.
        """

        # Gather parameters
        if input_str is None:
            input_str = ""
        if "%" in input_str or "_" in input_str:
            return create_response(
                message={"error": "fnome cannot contain % or _ characters"},
                status_code=STATUS_CODES["bad_request"],
            )

        # Log the operation
        log(
            log_type="info",
            message=(
                f"User {identity} requested fuzzy "
                f"search in classes with string {input_str}"
            ),
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
        )

        # Get the data
        data: List[Dict[str, Any]] = fetchall_query(
            query="SELECT sigla FROM classi WHERE sigla LIKE %s ORDER BY sigla DESC",
            params=(f"%{input_str}%",),
        )

        # Return the data
        return create_response(message=data, status_code=STATUS_CODES["ok"])

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def options(self) -> Response:
        """
        Handle OPTIONS request.
        This method is used to check which HTTP methods are allowed for this endpoint.
        """
        return handle_options_request(resource_class=self)


api.add_resource(Class, *Class.ENDPOINT_PATHS)
api.add_resource(ClassFromResponsible, *ClassFromResponsible.ENDPOINT_PATHS)
api.add_resource(ClassFuzzySearch, *ClassFuzzySearch.ENDPOINT_PATHS)
