"""
Utility functions for the API blueprints.
These functions include data validation, authorization checks, response creation,
database connection handling, logging, and token validation.
"""

import re
import inspect
import sys
import socket
import queue
import threading
from datetime import datetime, timezone
from os import getpid
from typing import Dict, List, Tuple, Any, Union
from functools import wraps
from contextlib import contextmanager
from flask import jsonify, make_response, request, Response, Request
from flask_jwt_extended import get_jwt_identity
from mysql.connector import pooling as mysql_pooling
from requests import post as requests_post
from requests.exceptions import RequestException
from cachetools import TTLCache
from config import (
    DB_HOST,
    REDACTED_USER,
    REDACTED_PASSWORD,
    DB_NAME,
    CONNECTION_POOL_SIZE,
    LOG_SERVER_HOST,
    LOG_SERVER_PORT,
    AUTH_SERVER_VALIDATE_URL,
    STATUS_CODES,
    ROLES,
    VALIDATION_REQUEST_TIMEOUT,
    SYSLOG_SEVERITY_MAP
)

# Data validation related
# Precompile the regex pattern once
SQL_PATTERN = re.compile(
    r"\b("
    + "|".join(
        [
            r"SELECT",
            r"INSERT",
            r"UPDATE",
            r"DELETE",
            r"DROP",
            r"CREATE",
            r"ALTER",
            r"EXEC",
            r"UNION",
            r"ALL",
            r"WHERE",
            r"FROM",
            r"TABLE",
            r"JOIN",
            r"TRUNCATE",
            r"REPLACE",
            r"GRANT",
            r"REVOKE",
            r"DECLARE",
            r"CAST",
            r"SET",
        ]
    )
    + r")\b",
    re.IGNORECASE,
)


def is_input_safe(data: Union[str, List[str], Dict[Any, str]]) -> bool:
    """
    Check if the input data (string, list, or dictionary) contains SQL instructions.
    Returns True if safe, False if potentially unsafe.

    :param data: str, list, or dict - The input data to validate.
    :return: bool - True if the input is safe, False otherwise.
    """
    if isinstance(data, str):
        return not bool(SQL_PATTERN.search(data))
    elif isinstance(data, list):
        return all(
            isinstance(item, str) and not bool(SQL_PATTERN.search(item))
            for item in data
        )
    elif isinstance(data, dict):
        return all(
            isinstance(value, str) and not bool(SQL_PATTERN.search(value))
            for value in data.values()
        )
    else:
        raise TypeError(
            "Input must be a string, list of strings, or dictionary with string values."
        )


def has_valid_json(request_instance: Request) -> Union[str, Dict[str, Any]]:
    """
    Check if the request has a valid JSON body.

    :param request: The Flask request object.
    :return: str or dict - The JSON data if valid, or an error string if invalid.
    """
    if not request_instance.is_json or request_instance.json is None:
        return "Request body must be valid JSON with Content-Type: application/json"
    try:
        data = request_instance.get_json(silent=False)
        return data if data != {} else "Request body must not be empty"
    except ValueError:
        return "Invalid JSON format"


def validate_json_request(request_instance: Request) -> Union[str, Dict[str, Any]]:
    """
    Check that a request that should contain a JSON body has a valid JSON body and is safe from SQL injection.
    If the request is valid, return the JSON data.
    Otherwise, return an error message.
    """

    # Validate request
    data: Union[str, Dict[str, Any]] = has_valid_json(request_instance)
    if isinstance(data, str):
        return data

    # Check for sql injection
    if not is_input_safe(data):
        return "invalid input, suspected sql injection"

    # If the request is valid, return the data
    return data


# Authorization related
def check_authorization(allowed_roles: List[str]):
    """
    Decorator to check if the user's role is in the allowed list.

    params:
        allowed_roles: List[str] - List of user roles that are permitted to execute the function.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract the user's role from the JWT
            identity = get_jwt_identity()
            if not identity or "role" not in identity:
                return create_response(
                    message={
                        "outcome": "not permitted: missing role or missing identity from jwt"
                    },
                    status_code=STATUS_CODES["forbidden"],
                )

            user_role: int = identity["role"]
            user_string: str = ROLES.get(
                user_role
            )  # Get corresponding natural language name of roles
            if (
                user_string not in allowed_roles
            ):  # (to allow for allowed_roles list to be the names of the roles and not their corresponding number)
                return create_response(
                    message={"outcome": "not permitted"},
                    status_code=STATUS_CODES["forbidden"],
                )

            # Proceed with the original function
            return func(*args, **kwargs)

        return wrapper

    return decorator


# Response related
def create_response(message: Dict, status_code: int) -> Response:
    """
    Create a response with a message and status code.

    params:
        message - The message to include in the response
        status_code - The HTTP status code to return

    returns:
        Response object with the message and status code

    raises:
        TypeError - If the message is not a dictionary or the status code is not an integer
    """

    if not isinstance(message, Dict):
        raise TypeError("Message must be a dictionary")

    # message = f"{message}\n{STATUS_CODES_EXPLANATIONS.get(status_code, 'Unknown status code')}"

    return make_response(jsonify(message), status_code)


def get_class_http_verbs(class_: type) -> List[str]:
    """
    Args:
        class (type): The class to inspect. Must be a class object, not an instance.
    Returns:
        list[str]: A list of HTTP verbs (in uppercase) implemented as methods in the class.
    Raises:
        TypeError: If the provided argument is not a class.
    """
    # Ensure the input is a class
    if not inspect.isclass(class_):
        raise TypeError(
            f"class_ must be a class, not an instance. Got {class_} instead."
        )

    # List of HTTP verbs to filter
    http_verbs = {
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
        "HEAD",
        "TRACE",
        "CONNECT",
    }

    # Get all methods of the class and filter by HTTP verbs
    return [verb for verb in http_verbs if hasattr(class_, verb.lower())]


# Data handling related
def parse_time_string(time_string: str) -> datetime:
    """
    Parse a time string in the format HH:MM and return a datetime object.

    params:
        time_string - The time string to parse

    returns:
        A datetime object if the string is in the correct format, None otherwise

    """

    try:
        return datetime.strptime(time_string, "%H:%M").time()
    except ValueError:
        return None


def parse_date_string(date_string: str) -> datetime:
    """
    Parse a date string in the format YYYY-MM-DD and return a datetime object.

    params:
        date_string - The date string to parse

    returns:
        A datetime object if the string is in the correct format, None otherwise

    """

    try:
        return datetime.strptime(date_string, "%Y-%m-%d").date()
    except ValueError:
        return None


# Database related
# Lazy initialization for the database connection pool
_DB_POOL = None  # Private variable to hold the connection pool instance


def get_db_pool():
    global _DB_POOL
    if _DB_POOL is None:  # Initialize only when accessed for the first time
        try:
            _DB_POOL = mysql_pooling.MySQLConnectionPool(
                pool_name="pctowa_connection_pool",
                pool_size=max(1, CONNECTION_POOL_SIZE),
                pool_reset_session=False,  # Session reset not needed for this application (no transactions)
                host=DB_HOST,
                user=REDACTED_USER,
                password=REDACTED_PASSWORD,
                database=DB_NAME,
            )
        except socket.error as ex:
            print(
                f"Couldn't access database, see next line for full exception.\n{ex}\n\n"
                "host: {DB_HOST}, dbname: {DB_NAME}, user: {REDACTED_USER}, password: {REDACTED_PASSWORD}"
            )
            sys.exit(1)
    return _DB_POOL


# Function to get a connection from the pool
@contextmanager  # Make a context manager to ensure the connection is closed after use
def get_db_connection():
    """
    Get a database connection from the pool using lazy initialization.
    """
    connection = get_db_pool().get_connection()  # Use the lazily initialized pool
    try:
        yield connection
    finally:
        connection.close()


# Function to clear the connection pool
def clear_db_connection_pool():
    """
    Clear the database connection pool by closing all connections.
    """
    global _DB_POOL
    for connection in _DB_POOL._cnx_queue:
        connection.close()
    _DB_POOL._cnx_queue.clear()


def build_select_query_from_filters(
    data, table_name, limit=1, offset=0
):  # TODO check if this function is necessary
    """
    Build a SQL query from filters.
    Does not support complex queries with joins or subqueries.

    params:
        data - The filters to apply to the query
        table_name - The name of the table to query
        limit - The maximum number of results to return
        offset - The offset for pagination

    returns:
        A tuple containing the query and the parameters to pass to the query

    raises:
        None
    """

    filters = " AND ".join([f"{key} = %s" for key in data.keys()])
    params = list(data.values()) + [limit, offset]
    query = f"SELECT * FROM {table_name} WHERE {filters} LIMIT %s OFFSET %s"
    return query, params


def build_update_query_from_filters(
    data, table_name, id_column, id_value
) -> Tuple[str, List[Any]]:
    """
    Build a SQL update query from filters.

    params:
        data - The filters to apply to the query
        table_name - The name of the table to query
        id_column - The name of the ID column to use for the update

    returns:
        A tuple containing the query and the parameters to pass to the query

    raises:
        None
    """

    filters = ", ".join([f"{key} = %s" for key in data.keys()])
    params = list(data.values()) + [id_value]
    query = f"UPDATE {table_name} SET {filters} WHERE {id_column} = %s"
    return query, params


# Graceful shutdown handler
def shutdown_handler():
    """
    Handle graceful shutdown of the application.
    """
    clear_db_connection_pool()
    print("Database connection pool cleared. Exiting...")
    sys.exit(0)


def fetchone_query(query: str, params: Tuple[Any]) -> Dict[str, Any]:
    """
    Execute a query on the database and return the result.

    params:
        query - The query to execute
        params - The parameters to pass to the query

    returns:
        The result of the query
    """

    with get_db_connection() as connection:  # Use a context manager to ensure the connection is closed after use
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()


def fetchall_query(query: str, params: Tuple[Any]) -> List[Dict[str, Any]]:
    """
    Execute a query on the database and return the result.
    """

    with get_db_connection() as connection:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()


def execute_query(query: str, params: Tuple[Any]) -> int:
    """
    Execute a query on the database and commit the changes.

    params:
        query - The query to execute
        params - The parameters to pass to the query

    returns:
        The ID of the last inserted row, if applicable
    """
    # Use a context manager to ensure the connection is closed after use
    with get_db_connection() as connection:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute(query, params)
            connection.commit()
            return cursor.lastrowid


# Log server related
# Create a queue for log messages
log_queue = queue.Queue()


def log_worker():
    """
    Background thread function to process log messages from the queue.
    """
    while True:
        # Get a log message from the queue
        log_data = log_queue.get()
        if log_data is None:  # Exit signal
            break

        # Extract log details
        type_, message, origin_name, origin_host, message_id, structured_data = log_data

        # Get the severity code for the log_type
        severity = SYSLOG_SEVERITY_MAP.get(type_, 6)  # Default to 'info' if not found

        # Format the syslog message with the correct priority
        priority = (1 * 8) + severity  # Assuming facility=1 (user-level messages)
        syslog_message = (
            f"<{priority}>1 "
            f"{datetime.now(timezone.utc).isoformat()} "  # Timestamp in ISO 8601 format with timezone
            f"{origin_host} "  # Hostname
            f"{origin_name} "  # App name
            f"{getpid()} "  # Process ID
            f"{message_id} "  # Message ID
            f"{structured_data} "  # Structured Data
            f"{message}"  # Log message
        )
        try:
            # Create a UDP socket and send the log message
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.sendto(
                    syslog_message.encode("utf-8"), (LOG_SERVER_HOST, LOG_SERVER_PORT)
                )
        except socket.error as ex:
            print(f"Failed to send log: {ex}")

        # Mark the task as done
        log_queue.task_done()


# Start the background thread
log_thread = threading.Thread(target=log_worker, daemon=True)
log_thread.start()


def log(
    log_type: str,
    message: str,
    origin_name: str,
    origin_host: str,
    message_id: str,
    structured_data: str = "- -",
) -> None:
    """
    Add a log message to the queue for the background thread to process.
    """
    log_queue.put(
        (log_type, message, origin_name, origin_host, message_id, structured_data)
    )


# Graceful shutdown function to stop the log thread
def shutdown_logging():
    """
    Signal the log thread to exit and wait for it to finish.
    """
    log_queue.put(None)  # Send exit signal
    log_thread.join()  # Wait for the thread to finish (even if it is a daemon thread so no logs are lost)


# Token validation related
# | Create a cache for token validation results with a time-to-live (TTL) of 600 seconds (10 minutes)
token_cache = TTLCache(maxsize=5000, ttl=600)


def jwt_required_endpoint(func: callable) -> callable:
    """
    Decorator to check if the JWT token is valid and cache the result.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Extract the token from the Authorization header
        def get_bearer_token():
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                return auth_header[len("Bearer ") :]
            return None

        token = get_bearer_token()
        if not token:
            return create_response(
                message={"error": "missing token"},
                status_code=STATUS_CODES["unauthorized"],
            )

        # Check token cache
        cached_result = token_cache.get(token)
        if cached_result:
            is_valid, identity = cached_result
        else:
            try:

                # Headers (e.g., Authorization token)
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                }

                # Send a POST request to the auth server to validate the token
                response = requests_post(
                    url=AUTH_SERVER_VALIDATE_URL,
                    headers=headers,
                    timeout=VALIDATION_REQUEST_TIMEOUT,
                )
                response.raise_for_status()  # Raise exception for HTTP errors

                if response.status_code != STATUS_CODES[
                    "ok"
                ] or not response.json().get("valid"):
                    return create_response(
                        message={"error": "Invalid or expired token"},
                        status_code=STATUS_CODES["unauthorized"],
                    )

                is_valid = response.json().get("valid")
                identity = response.json().get("identity")
                token_cache[token] = (is_valid, identity)

            except RequestException as e:
                return create_response(
                    message={"error": f"Authentication server error: {str(e)}"},
                    status_code=STATUS_CODES["service_unavailable"],
                )

        # Pass the identity to the wrapped function
        return func(*args, **kwargs, identity=identity)

    return wrapper
