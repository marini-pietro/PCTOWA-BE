# Define authentication server data
AUTH_SERVER_HOST = 'localhost' # The host of the authentication server
AUTH_SERVER_PORT = 5002 # The port of the authentication server
AUTH_SERVER_VALIDATE_URL = f'http://{AUTH_SERVER_HOST}:{AUTH_SERVER_PORT}/auth/validate' # The URL to validate a token
AUTH_SERVER_NAME_IN_LOG = 'auth-server'
AUTH_SERVER_DEBUG_MODE = True
JWT_TOKEN_DURATION = 3 # In hours

# Define log server host, port and server name in log files
LOG_SERVER_HOST = 'localhost' # The host of the log server
LOG_SERVER_PORT = 5001 # The port of the log server
LOG_SERVER_DEBUG_MODE = True

# Define host and port of the API server
API_SERVER_HOST = '172.16.1.98' # The host of the API server (should be only server open to the rest of the network)
API_SERVER_PORT = 5000 # The port of the API server
API_SERVER_NAME_IN_LOG = 'api-server' # The name of the server in the log messages
API_SERVER_DEBUG_MODE = True

# Database configuration
DB_HOST = "localhost"
DB_NAME = "pctowa"
DB_USER = "pctowa"
DB_PASSWORD = "pctowa2025"
CONNECTION_POOL_SIZE = 20 # The maximum number of connections in the pool

# HTTP status codes and their explanations
STATUS_CODES_EXPLANATIONS = {
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
    503: "Service Unavailable - The server is not ready to handle the request."
}

STATUS_CODES = {
    "not_found": 404,
    "unauthorized": 401,
    "forbidden": 403,
    "bad_request": 400,
    "created": 201,
    "ok": 200,
    "internal_error": 500,
}

# Authorization related
ROLES = {
    0: "admin",
    1: "teacher",
    2: "tutor",
    3: "supertutor"
}

NOT_AUTHORIZED_MESSAGE: dict[str, str] = {'outcome': 'error, action not permitted with current user'}