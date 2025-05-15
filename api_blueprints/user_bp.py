"""
User management module for the API.
This module provides endpoints for user registration, login, and management.
It includes the following functionalities:
- User registration
- User login
- User deletion
- User update
- User binding to a company
- Fetching the list of reference teachers associated with a given company or class
- Fetching the list of users associated with a given company or class
"""

import os
import base64
from os.path import basename as os_path_basename
from typing import List, Dict, Any
from flask import Blueprint, request, Response
from flask_restful import Api, Resource
from marshmallow import fields, ValidationError
from marshmallow.validate import OneOf
from requests import post as requests_post
from requests.exceptions import RequestException
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from mysql.connector import IntegrityError

from config import (
    AUTH_SERVER_HOST,
    AUTH_SERVER_PORT,
    STATUS_CODES,
    LOGIN_AVAILABLE_THROUGH_API,
    AUTH_SERVER_SSL,
    ROLES,
)
from api_server import ma

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

# Create the blueprint and API
user_bp = Blueprint(BP_NAME, __name__)
api = Api(user_bp)


# Define a Marshmallow schema for user registration
class UserSchema(ma.Schema):
    """
    Schema for validating and deserializing user data.
    """

    email = fields.Email(
        required=True,
        error_messages={
            "required": "email is required.",
            "invalid": "email must be a valid email address.",
        },
    )
    password = fields.String(
        required=True, error_messages={"required": "password is required."}
    )
    nome = fields.String(
        required=True, error_messages={"required": "nome is required."}
    )
    cognome = fields.String(
        required=True, error_messages={"required": "cognome is required."}
    )
    ruolo = fields.String(
        required=True,
        validate=OneOf(ROLES, error="ruolo must be one of the allowed roles."),
        error_messages={"required": "ruolo is required."},
    )


user_schema = UserSchema()


def hash_password(password: str) -> str:
    """
    Hash a password using PBKDF2 with SHA-256.
    Args:
        password (str): The password to hash.
    Returns:
        str: The hashed password.
    """
    # Generate a random salt
    salt = os.urandom(16)  # 16 bytes (128 bits)
    # Use PBKDF2 to hash the password
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),  # 256 bits (32 byte)
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend(),
    )
    hashed_password = base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))
    # Store the salt and hashed password together
    return f"{base64.urlsafe_b64encode(salt).decode('utf-8')}:{hashed_password.decode('utf-8')}"


class User(Resource):
    """
    User resource for managing user data.
    This class handles the following HTTP methods:
    - POST: Create a new user
    - DELETE: Delete a user by email
    - PATCH: Update a user by email
    - GET: Get a user by email
    - OPTIONS: Get allowed HTTP methods for this endpoint
    """

    ENDPOINT_PATHS = [f"/{BP_NAME}", f"/{BP_NAME}/<string:email>"]

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin"])
    def post(self, identity) -> Response:
        """
        Register a new user.
        The request body must be a JSON object with application/json content type.
        """

        # Validate and deserialize input using Marshmallow
        try:
            data = user_schema.load(request.get_json())
        except ValidationError as err:
            return create_response(
                message={"errors": err.messages},
                status_code=STATUS_CODES["bad_request"],
            )

        email: str = data["email"]
        password: str = data["password"]
        name: str = data["nome"]
        surname: str = data["cognome"]
        ruolo: int = data["ruolo"]

        # Hash the password before storing it
        hashed_password = hash_password(password)

        try:
            lastrowid, _ = execute_query(
                "INSERT INTO utenti (email_utente, password, nome, cognome, ruolo) "
                "VALUES (%s, %s, %s, %s, %s)",
                (email, hashed_password, name, surname, ruolo),
            )

            # Log the register
            log(
                log_type="info",
                message=f"User {identity} registered user {email}",
                structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
            )

            # Return success message
            return create_response(
                message={
                    "outcome": "user successfully created",
                    "location": get_hateos_location_string(bp_name=BP_NAME, id_=email),
                },
                status_code=STATUS_CODES["created"],
            )
        except IntegrityError as ex:
            # Log the error
            log(
                log_type="error",
                message=(
                    f"User {identity} tried to "
                    f"register user {email} but it already generated {ex}"
                ),
                structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
            )

            # Return error message
            return create_response(
                message={
                    "outcome": "error, user with provided credentials already exists"
                },
                status_code=STATUS_CODES["bad_request"],
            )

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin"])
    def delete(self, email, identity) -> Response:
        """
        Delete an existing user.
        The id_ is passed as a path variable.
        """

        # Validate parameters TODO add regex check for email format

        # Delete the user
        _, rows_affected = execute_query(
            "DELETE FROM utente WHERE email_utente = %s", (email,)
        )

        # Check if any rows were affected
        if rows_affected == 0:
            return create_response(
                message={"error": "user with provided email does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        # Log the deletion
        log(
            log_type="info",
            message=f"User {identity} deleted user {email}",
            structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
        )

        # Return success message
        return create_response(
            message={"outcome": "user successfully deleted"},
            status_code=STATUS_CODES["no_content"],
        )

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin"])
    def patch(self, email, identity) -> Response:
        """
        Update an existing user.
        The id_ is passed as a path variable.
        """

        # Gather parameters
        data = request.get_json()

        # Check if user exists using EXISTS keyword
        user_exists: bool = fetchone_query(
            "SELECT EXISTS(SELECT 1 FROM utente WHERE email_utente = %s) AS ex",
            (email,),
        )["ex"]
        if not user_exists:
            return create_response(
                message={"outcome": "error, user with provided email does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        # Check that the specified fields actually exist in the database
        temp = check_column_existence(
            modifiable_columns=[
                "email_utente",
                "password",
                "nome",
                "cognome",
                "tipo",
            ],
            to_modify=list(data.keys()),
        )
        if isinstance(temp, str):
            return create_response(
                message={"error": temp}, status_code=STATUS_CODES["bad_request"]
            )

        # Build the update query
        query, params = build_update_query_from_filters(
            data=data, table_name="utenti", pk_column="email_utente", pk_value=email
        )

        # Update the user
        execute_query(query, params)

        # Log the update
        log(
            log_type="info",
            message=f"User {identity} updated user {email}",
            structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
        )

        # Return success message
        return create_response(
            message={"outcome": "user successfully updated"},
            status_code=STATUS_CODES["ok"],
        )

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin"])
    def get(self, identity) -> Response:
        """
        Get all users, can be filtered by role.
        """

        # Gather query strings
        role: str = request.args.get("ruolo", type=str)
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

        # Validate query strings
        if role and role not in ROLES:
            return create_response(
                message={"error": "unknown role value"},
                status_code=STATUS_CODES["bad_request"],
            )

        # Build query
        query = "SELECT * FROM utenti"
        params = []

        if role:
            query += " WHERE ruolo = %s"
            params.append(role)

        query += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        # Execute query
        users: List[Dict[str, Any]] = fetchall_query(query, tuple(params))

        # Handle empty results
        if users is None:
            return create_response(
                message={"error": "no users found"},
                status_code=STATUS_CODES["not_found"],
            )

        # Log the read
        log(
            log_type="info",
            message=f"User {identity} requested user list",
            structured_data=f"[endpoint='{request.path} verb='{request.method}']",
        )

        # Return the list of users
        return create_response(message=users, status_code=STATUS_CODES["ok"])

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def options(self) -> Response:
        """
        Handle OPTIONS request for CORS preflight.
        This method returns the allowed HTTP methods for this endpoint.
        """

        return handle_options_request(resource_class=self)


class UserLoginSchema(ma.Schema):
    """
    Schema for validating and deserializing user login data.
    """

    email = fields.Email(required=True)
    password = fields.String(required=True)


user_login_schema = UserLoginSchema()


class UserLogin(Resource):
    """
    User login resource for managing user authentication.
    This class handles the following HTTP methods:
    - POST: User login
    - OPTIONS: Get allowed HTTP methods for this endpoint
    """

    ENDPOINT_PATHS = [f"/{BP_NAME}/auth/login"]

    def post(self) -> Response:
        """
        User login endpoint.
        The request body must be a JSON object with application/json content type.
        """

        # Check if login is available through the API server
        if not LOGIN_AVAILABLE_THROUGH_API:
            return create_response(
                message={
                    "error": "login not available through API server, "
                    "contact authentication service directly"
                },
                status_code=STATUS_CODES["forbidden"],
            )

        # Validate and deserialize input using Marshmallow
        try:
            data = user_login_schema.load(request.get_json())
        except ValidationError as err:
            return create_response(
                message={"errors": err.messages},
                status_code=STATUS_CODES["bad_request"],
            )

        email: str = data["email"]
        password: str = data["password"]

        try:
            # Forward login request to the authentication service
            response = requests_post(
                f"{'https' if AUTH_SERVER_SSL else 'http'}://{AUTH_SERVER_HOST}:{AUTH_SERVER_PORT}/auth/login",
                json={"email": email, "password": password},
                timeout=5,
            )
        except RequestException as ex:

            # Log the error
            log(
                log_type="error",
                message=f"Authentication service unavailable: {str(ex)}",
                structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
            )

            # Return error response
            return create_response(
                message={"error": "authentication service unavailable"},
                status_code=STATUS_CODES["internal_error"],
            )

        # Handle response from the authentication service
        if (
            response.status_code == STATUS_CODES["ok"]
        ):  # If the login is successful, send the token back to the user

            # Logging login is already handled by auth server

            return create_response(
                message=response.json(), status_code=STATUS_CODES["ok"]
            )

        if response.status_code == STATUS_CODES["unauthorized"]:
            log(
                log_type="warning",
                message=f"Failed login attempt for email: {email}",
                structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
            )
            return create_response(
                message={"error": "Invalid credentials"},
                status_code=STATUS_CODES["unauthorized"],
            )

        elif response.status_code == STATUS_CODES["bad_request"]:
            log(
                log_type="error",
                message=f"Bad request during login for email: {email}",
                structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
            )
            return create_response(
                message={"error": "Bad request"},
                status_code=STATUS_CODES["bad_request"],
            )

        elif response.status_code == STATUS_CODES["internal_error"]:
            log(
                log_type="error",
                message=f"Internal error during login for email: {email}",
                structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
            )
            return create_response(
                message={"error": "Internal error"},
                status_code=STATUS_CODES["internal_error"],
            )

        else:
            log(
                log_type="error",
                message=(
                    f"Unexpected error during login for email: {email} "
                    f"with status code: {response.status_code}"
                ),
                structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
            )
            return create_response(
                message={"error": "Unexpected error during login"},
                status_code=STATUS_CODES["internal_error"],
            )

    def options(self) -> Response:
        """
        Handle OPTIONS request for CORS preflight.
        This method returns the allowed HTTP methods for this endpoint.
        """
        return handle_options_request(resource_class=self)


class BindUserToCompanySchema(ma.Schema):
    """
    Schema for validating and deserializing user binding data.
    """

    id_azienda = fields.Integer(
        required=True,
        validate=lambda x: x > 0,
        error_messages={"invalid": "id_azienda must be a positive integer."},
    )


bind_user_to_company_schema = BindUserToCompanySchema()


class BindUserToCompany(Resource):
    """
    Bind a user to a company.
    This class handles the following HTTP methods:
    - POST: Bind a user to a company
    - OPTIONS: Get allowed HTTP methods for this endpoint
    """

    ENDPOINT_PATHS = [f"/{BP_NAME}/bind/<string:email>"]

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin"])
    def post(self, email, identity) -> Response:
        """
        Bind a user to a company.
        The id_ is passed as a path variable.
        """

        # Validate and deserialize input using Marshmallow
        try:
            data = bind_user_to_company_schema.load(request.get_json())
        except ValidationError as err:
            return create_response(
                message={"errors": err.messages},
                status_code=STATUS_CODES["bad_request"],
            )

        company_id: int = data["id_azienda"]

        # Check if user exists using EXISTS keyword
        user_exists: bool = fetchone_query(
            "SELECT EXISTS(SELECT 1 FROM utenti WHERE email_utente = %s) AS ex",
            (email,),
        )["ex"]
        if not user_exists:
            return create_response(
                message={"outcome": "error, user with provided email does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        # Check if company exists using EXISTS keyword
        company_exists: bool = fetchone_query(
            "SELECT EXISTS(SELECT 1 FROM aziende WHERE id_azienda = %s) AS ex",
            (company_id,),
        )["ex"]
        if not company_exists:
            return create_response(
                message={"outcome": "error, company with provided id_ does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        # Bind the user to the company
        try:
            execute_query(
                "UPDATE utenti SET company_id = %s WHERE email_utente = %s",
                (company_id, email),
            )
        except IntegrityError as ex:
            log(
                log_type="error",
                message=(
                    f"User {identity.get('email')} tried to bind user {email} "
                    f"to company {company_id} but it already generated {ex}"
                ),
                structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
            )
            return create_response(
                message={"error": "conflict error"},
                status_code=STATUS_CODES["conflict"],
            )
        except Exception as ex:
            log(
                log_type="error",
                message=(
                    f"User {identity} failed to bind user {email} "
                    f"to company {company_id} with error: {str(ex)}"
                ),
                structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
            )
            return create_response(
                message={"error": "internal server error"},
                status_code=STATUS_CODES["internal_error"],
            )

        # Log the binding
        log(
            log_type="info",
            message=(f"User {identity} bound " f"user {email} to company {company_id}"),
            structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
        )

        # Return success message
        return create_response(
            message={"outcome": "user successfully bound to company"},
            status_code=STATUS_CODES["ok"],
        )

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def options(self) -> Response:
        """
        This method returns the allowed HTTP methods for this endpoint.
        """
        return handle_options_request(resource_class=self)


class ReadBindedUser(Resource):
    """
    Read the list of reference teachers associated with a given company or class.
    This class handles the following HTTP methods:
    - GET: Get the list of reference teachers associated with a given company or class
    - OPTIONS: Get allowed HTTP methods for this endpoint
    """

    ENDPOINT_PATHS = [f"/{BP_NAME}/binded/<string:id_>"]

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def get(self, id_, identity) -> Response:
        """
        Get the list of the reference teachers associated with a given company or class.
        The company or class is passed as a path variable id_.
        The id_type is passed as a query parameter.
        The id_type can be either 'company' or 'class'.
        """

        # Validate parameters
        if id_ < 0:
            return create_response(
                message={"error": "id must be a positive integer"},
                status_code=STATUS_CODES["bad_request"],
            )

        # Gather parameters
        id_type: str = request.args.get("id_type")

        # Log the read
        log(
            log_type="info",
            message=(
                f"User {identity} requested reference "
                f"teacher list with {id_type} and id_ {id_}"
            ),
            structured_data=f"[endpoint='{request.path}' verb='{request.method}']",
        )

        # Validate parameters
        if id_type is None:
            return create_response(
                message={"error": "missing id_type"},
                status_code=STATUS_CODES["bad_request"],
            )
        if id_type not in ["company", "class"]:
            return create_response(
                message={"error": "id_type must be either company or class"},
                status_code=STATUS_CODES["bad_request"],
            )

        # Check that the specified resource exist
        if id_type == "company":
            company_exists: bool = fetchone_query(
                "SELECT EXISTS(SELECT 1 FROM aziende WHERE id_azienda = %s) AS ex",
                (id_,),
            )["ex"]
            if not company_exists:
                return create_response(
                    message={"outcome": "error, specified company does not exist"},
                    status_code=STATUS_CODES["not_found"],
                )

            # Build query
            query: str = (
                "SELECT U.email_utente, U.nome, U.cognome, RT.anno "
                "FROM docente_referente AS RT JOIN utenti AS U "
                "ON U.email_utente = RT.docente_referente "
                "WHERE RT.id_azienda = %s"
            )

        # Check that the specified resource exist
        elif id_type == "class":
            class_exists: bool = fetchone_query(
                "SELECT EXISTS(SELECT 1 FROM classi WHERE id_classe = %s) AS ex",
                (id_,),
            )["ex"]
            if not class_exists:
                return create_response(
                    message={"outcome": "error, specified class does not exist"},
                    status_code=STATUS_CODES["not_found"],
                )

            query: str = (
                "SELECT U.email_utente, U.nome, U.cognome, C.anno "
                "FROM classi AS C JOIN utenti AS U ON U.email_utente = C.email_responsabile "
                "WHERE C.id_classe = %s"
            )

        # Get the list of associated users
        resources: List[Dict[str, Any]] = fetchall_query(query, (id_,))

        # Return the list of users
        return create_response(message=resources, status_code=STATUS_CODES["ok"])

    @jwt_validation_required
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def options(self) -> Response:
        """
        This method returns the allowed HTTP methods for this endpoint.
        """

        return handle_options_request(resource_class=self)


# Add resources to the API
api.add_resource(User, *User.ENDPOINT_PATHS)
api.add_resource(UserLogin, *UserLogin.ENDPOINT_PATHS)
api.add_resource(BindUserToCompany, *BindUserToCompany.ENDPOINT_PATHS)
api.add_resource(ReadBindedUser, *ReadBindedUser.ENDPOINT_PATHS)
