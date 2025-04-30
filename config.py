"""
This module contains the configuration settings for the API server, including:
- Authentication server settings
- Log server settings
- API server settings
- Database settings
- HTTP status codes and their explanations
- Authorization settings
"""

from typing import Dict

# Define authentication server data
AUTH_SERVER_HOST: str = "localhost"  # The host of the authentication server
AUTH_SERVER_PORT: int = 6002  # The port of the authentication server
AUTH_SERVER_VALIDATE_URL: str = (
    f"http://{AUTH_SERVER_HOST}:{AUTH_SERVER_PORT}/auth/validate"  # The URL to validate a token
)
AUTH_SERVER_NAME_IN_LOG: str = "auth-server"
AUTH_SERVER_DEBUG_MODE: bool = True
JWT_TOKEN_DURATION: int = 3  # In hours
JWT_SECRET_KEY: str = "Lorem ipsum dolor sit amet eget."
VALIDATION_REQUEST_TIMEOUT: int = 3  # In seconds

# Define log server host, port and server name in log files
LOG_SERVER_HOST: str = "localhost"  # The host of the log server
LOG_SERVER_PORT: int = (
    6014  # The port of the log server (default syslog port, can modified to open port for testing)
)
LOG_FILE_NAME: str = "pctowa_log.txt"
LOGGER_NAME: str = "pctowa_logger"  # The name of the logger
LOG_SERVER_NAME_IN_LOG: str = "log-server"  # The name of the server in the log messages
RATE_LIMIT = 100  # Maximum messages per source
TIME_WINDOW = 1  # Time window in seconds
DELAYED_LOGS_QUEUE_SIZE = 100  # The size of the delayed logs queue (if the queue is full, the oldest logs will be removed to make space for new ones)
# Define a severity map for the syslog server
SYSLOG_SEVERITY_MAP: Dict[str, int] = {
    "emergency": 0,  # System is unusable
    "alert": 1,      # Action must be taken immediately
    "critical": 2,   # Critical conditions
    "error": 3,      # Error conditions
    "warning": 4,    # Warning conditions
    "notice": 5,     # Normal but significant condition
    "info": 6,  # Informational messages
    "debug": 7       # Debug-level messages
}

# Define host and port of the API server
API_SERVER_HOST: str = (
    "172.16.1.98"  # The host of the API server (should be only server open to the rest of the network)
)
API_SERVER_PORT: int = 6000  # The port of the API server
API_SERVER_NAME_IN_LOG: str = "api-server"  # The name of the server in the log messages
API_VERSION: str = "v1"  # The version of the API
URL_PREFIX: str = f"/api/{API_VERSION}/"
API_SERVER_DEBUG_MODE: bool = True

# Database configuration
DB_HOST: str = "localhost"
DB_NAME: str = "pctowa"
DB_USER: str = "abc"
DB_PASSWORD: str = "123"
CONNECTION_POOL_SIZE: int = 20  # The maximum number of connections in the pool

# HTTP status codes and their explanations
STATUS_CODES_EXPLANATIONS: Dict[int, str] = {
    200: "OK - The request has succeeded.",
    201: "Created - The request has been fulfilled and resulted in a new resource being created.",
    202: "Accepted - The request has been accepted for processing, but the processing has not been completed.",
    204: "No Content - The server successfully processed the request, but is not returning any content.",
    400: "Bad Request - The server could not understand the request due to invalid syntax.",
    401: "Unauthorized - The client must authenticate itself to get the requested response.",
    403: "Forbidden - The client does not have access rights to the content.",
    404: "Not Found - The server can not find the requested resource.",
    405: "Method Not Allowed - The request method is known by the server but is not supported by the target resource.",
    409: "Conflict - The request could not be completed due to a conflict with the current state of the resource.",
    500: "Internal Server Error - The server has encountered a situation it doesn't know how to handle.",
    502: "Bad Gateway - The server was acting as a gateway or proxy and received an invalid response from the upstream server.",
    503: "Service Unavailable - The server is not ready to handle the request.",
}

STATUS_CODES: Dict[str, int] = {
    "not_found": 404,
    "unauthorized": 401,
    "forbidden": 403,
    "conflict": 409,
    "bad_request": 400,
    "created": 201,
    "ok": 200,
    "no_content": 204,
    "internal_error": 500,
    "service_unavailable": 503,
}

# Authorization related
ROLES = {0: "admin", 1: "teacher", 2: "tutor", 3: "supertutor"}

NOT_AUTHORIZED_MESSAGE: Dict[str, str] = {
    "outcome": "error, action not permitted with current user"
}
