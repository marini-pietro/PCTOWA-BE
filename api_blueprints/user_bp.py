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

from os.path import basename as os_path_basename
from typing import List, Dict, Any, Union
from flask import Blueprint, request, Response
from flask_restful import Api, Resource
from flask_jwt_extended import get_jwt_identity, jwt_required
from requests import post as requests_post
from requests.exceptions import RequestException
from mysql.connector import IntegrityError

from config import (
    API_SERVER_HOST,
    API_SERVER_NAME_IN_LOG,
    AUTH_SERVER_HOST,
    AUTH_SERVER_PORT,
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
    validate_json_request,
    check_column_existence,
    get_hateos_location_string,
)

# Define constants
BP_NAME = os_path_basename(__file__).replace("_bp.py", "")

# Create the blueprint and API
user_bp = Blueprint(BP_NAME, __name__)
api = Api(user_bp)


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

    @jwt_required()
    @check_authorization(allowed_roles=["admin"])
    def post(self) -> Response:
        """
        Register a new user.
        The request body must be a JSON object with application/json content type.
        """

        # Validate request
        data = validate_json_request(request)
        if isinstance(data, str):
            return create_response(
                message={"error": data}, status_code=STATUS_CODES["bad_request"]
            )

        # Gather parameters
        email: str = data.get("email")
        password: str = data.get("password")
        name: str = data.get("nome")
        surname: str = data.get("cognome")
        user_type: int = data.get("tipo")

        try:
            lastrowid: int = execute_query(
                "INSERT INTO utenti (email_utente, password, nome, cognome, tipo) "
                "VALUES (%s, %s, %s, %s, %s)",
                (email, password, name, surname, int(user_type)),
            )

            # Log the register
            log(
                log_type="info",
                message=f"User {get_jwt_identity()} registered user {email}",
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                message_id="UserAction",
                structured_data=f"[endpoint={User.ENDPOINT_PATHS[0]} verb='POST']",
            )

            # Return success message
            return create_response(
                message={
                    "outcome": "user successfully created",
                    "location": get_hateos_location_string(
                        bp_name=BP_NAME, id_=lastrowid
                    ),
                },
                status_code=STATUS_CODES["created"],
            )
        except IntegrityError as ex:

            # Log the error
            log(
                log_type="error",
                message=(
                    f"User {get_jwt_identity()} tried to "
                    f"register user {email} but it already generated {ex}"
                ),
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                message_id="UserAction",
                structured_data={
                    "endpoint": User.ENDPOINT_PATHS[0],
                    "verb": "POST",
                },
            )

            # Return error message
            return create_response(
                message={
                    "outcome": "error, user with provided credentials already exists"
                },
                status_code=STATUS_CODES["bad_request"],
            )

    @jwt_required()
    @check_authorization(allowed_roles=["admin"])
    def delete(self, email) -> Response:
        """
        Delete an existing user.
        The id_ is passed as a path variable.
        """

        # Check if user exists
        user: Dict[str, Any] = fetchone_query(
            "SELECT nome FROM utente WHERE email_utente = %s", (email,)
        )
        if user is None:
            return create_response(
                message={"error": "user with provided email does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        # Delete the user
        execute_query("DELETE FROM utente WHERE email_utente = %s", (email,))

        # Log the deletion
        log(
            log_type="info",
            message=f"User {get_jwt_identity()} deleted user {email}",
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={"endpoint": User.ENDPOINT_PATHS[1], "verb": "DELETE"},
        )

        # Return success message
        return create_response(
            message={"outcome": "user successfully deleted"},
            status_code=STATUS_CODES["no_content"],
        )

    @jwt_required()
    @check_authorization(allowed_roles=["admin"])
    def patch(self, email) -> Response:
        """
        Update an existing user.
        The id_ is passed as a path variable.
        """

        # Validate request
        data = validate_json_request(request)
        if isinstance(data, str):
            return create_response(
                message={"error": data}, status_code=STATUS_CODES["bad_request"]
            )

        # Check if user exists
        user: Dict[str, Any] = fetchone_query(
            "SELECT nome FROM utente WHERE email_utente = %s",
            (email,),  # Only check for existence (SELECT column could be any field)
        )
        if user is None:
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
            message=f"User {get_jwt_identity()} updated user {email}",
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={"endpoint": User.ENDPOINT_PATHS[1], "verb": "PATCH"},
        )

        # Return success message
        return create_response(
            message={"outcome": "user successfully updated"},
            status_code=STATUS_CODES["ok"],
        )

    # TODO GET method to get all user for an admin page???

    @jwt_required()
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def options(self) -> Response:
        """
        Handle OPTIONS request for CORS preflight.
        This method returns the allowed HTTP methods for this endpoint.
        """

        return handle_options_request(resource_class=self)


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

        # Validate request
        data = validate_json_request(request)
        if isinstance(data, str):
            return create_response(
                message={"error": data}, status_code=STATUS_CODES["bad_request"]
            )

        # Gather parameters
        email: str = data.get("email")
        password: str = data.get("password")

        # Validate parameters
        if email is None or password is None or email == "" or password == "":
            return create_response(
                message={"error": "missing email or password"},
                status_code=STATUS_CODES["bad_request"],
            )

        try:
            # Forward login request to the authentication service
            response = requests_post(
                f"http://{AUTH_SERVER_HOST}:{AUTH_SERVER_PORT}/auth/login",
                json={"email": email, "password": password},
                timeout=5,
            )
        except RequestException as ex:

            # Log the error
            log(
                log_type="error",
                message=f"Authentication service unavailable: {str(ex)}",
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                message_id="UserAction",
                structured_data={
                    "endpoint": UserLogin.ENDPOINT_PATHS[0],
                    "verb": "POST",
                },
            )

            # Return error response
            return create_response(
                message={"error": "Authentication service unavailable"},
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
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                message_id="UserAction",
                structured_data={
                    "endpoint": UserLogin.ENDPOINT_PATHS[0],
                    "verb": "POST",
                },
            )
            return create_response(
                message={"error": "Invalid credentials"},
                status_code=STATUS_CODES["unauthorized"],
            )

        elif response.status_code == STATUS_CODES["bad_request"]:
            log(
                log_type="error",
                message=f"Bad request during login for email: {email}",
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                message_id="UserAction",
                structured_data={
                    "endpoint": UserLogin.ENDPOINT_PATHS[0],
                    "verb": "POST",
                },
            )
            return create_response(
                message={"error": "Bad request"},
                status_code=STATUS_CODES["bad_request"],
            )

        elif response.status_code == STATUS_CODES["internal_error"]:
            log(
                log_type="error",
                message=f"Internal error during login for email: {email}",
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                message_id="UserAction",
                structured_data={
                    "endpoint": UserLogin.ENDPOINT_PATHS[0],
                    "verb": "POST",
                },
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
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                message_id="UserAction",
                structured_data=f"[endpoint='{UserLogin.ENDPOINT_PATHS[0]} verb='POST']",
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


class BindUserToCompany(Resource):
    """
    Bind a user to a company.
    This class handles the following HTTP methods:
    - POST: Bind a user to a company
    - OPTIONS: Get allowed HTTP methods for this endpoint
    """

    ENDPOINT_PATHS = [f"/{BP_NAME}/bind/<string:email>"]

    @jwt_required()
    @check_authorization(allowed_roles=["admin"])
    def post(self, email) -> Response:
        """
        Bind a user to a company.
        The id_ is passed as a path variable.
        """

        # Validate request
        data = validate_json_request(request)
        if isinstance(data, str):
            return create_response(
                message={"error": data}, status_code=STATUS_CODES["bad_request"]
            )

        # Gather parameters
        company_id: Union[str, int] = data.get("id_azienda")

        # Validate parameters
        if company_id is None:
            return create_response(
                message={"error": "missing company id_"},
                status_code=STATUS_CODES["bad_request"],
            )
        try:
            company_id = int(company_id)
        except ValueError:
            return create_response(
                message={"error": "company id_ must be an integer"},
                status_code=STATUS_CODES["bad_request"],
            )

        # Check if user exists
        user: Dict[str, Any] = fetchone_query(
            "SELECT nome FROM utenti WHERE email_utente = %s",
            (email,),  # Only check for existence (SELECT column could be any field)
        )
        if user is None:
            return create_response(
                message={"outcome": "error, user with provided email does not exist"},
                status_code=STATUS_CODES["not_found"],
            )

        # Check if company exists
        company: Dict[str, Any] = fetchone_query(
            "SELECT fax FROM aziende WHERE id_azienda = %s",
            (
                company_id,
            ),  # Only check for existence (SELECT column could be any field)
        )
        if company is None:
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
                    f"User {get_jwt_identity().get('email')} tried to bind user {email} "
                    f"to company {company_id} but it already generated {ex}"
                ),
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                message_id="UserAction",
                structured_data={
                    "endpoint": BindUserToCompany.ENDPOINT_PATHS[0],
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
                message=(
                    f"User {get_jwt_identity()} failed to bind user {email} "
                    f"to company {company_id} with error: {str(ex)}"
                ),
                origin_name=API_SERVER_NAME_IN_LOG,
                origin_host=API_SERVER_HOST,
                message_id="UserAction",
                structured_data={
                    "endpoint": BindUserToCompany.ENDPOINT_PATHS[0],
                    "verb": "POST",
                },
            )
            return create_response(
                message={"error": "internal server error"},
                status_code=STATUS_CODES["internal_error"],
            )

        # Log the binding
        log(
            log_type="info",
            message=(
                f"User {get_jwt_identity()} bound "
                f"user {email} to company {company_id}"
            ),
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={
                "endpoint": BindUserToCompany.ENDPOINT_PATHS[0],
                "verb": "POST",
            },
        )

        # Return success message
        return create_response(
            message={"outcome": "user successfully bound to company"},
            status_code=STATUS_CODES["ok"],
        )

    @jwt_required()
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

    @jwt_required()
    @check_authorization(allowed_roles=["admin", "supertutor", "tutor", "teacher"])
    def get(self, id_) -> Response:
        """
        Get the list of the reference teachers associated with a given company or class.
        The company or class is passed as a path variable id_.
        The id_type is passed as a query parameter.
        The id_type can be either 'company' or 'class'.
        """

        # Gather parameters
        id_type: str = request.args.get("id_type")

        # Log the read
        log(
            log_type="info",
            message=(
                f"User {get_jwt_identity()} requested reference "
                f"teacher list with {id_type} and id_ {id_}"
            ),
            origin_name=API_SERVER_NAME_IN_LOG,
            origin_host=API_SERVER_HOST,
            message_id="UserAction",
            structured_data={
                "endpoint": ReadBindedUser.ENDPOINT_PATHS[0],
                "verb": "GET",
            },
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
            company: Dict[str, Any] = fetchone_query(
                "SELECT fax FROM aziende WHERE id_azienda = %s",
                (id_,),  # Only check for existence (SELECT column could be any field)
            )
            if not company:
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
            class_: Dict[str, Any] = fetchone_query(
                "SELECT sigla FROM classi WHERE id_classe = %s",
                (id_,),  # Only check for existence (SELECT column could be any field)
            )
            if not class_:
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

    @jwt_required()
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
