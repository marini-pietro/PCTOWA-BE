# Define authentication server data
AUTH_SERVER_HOST = 'localhost' # The host of the authentication server
AUTH_SERVER_PORT = 5002 # The port of the authentication server
AUTH_SERVER_VALIDATE_URL = f'http://{AUTH_SERVER_HOST}:{AUTH_SERVER_PORT}/auth/validate' # The URL to validate a token

# Define log server host, port and server name in log files
LOG_SERVER_HOST = 'localhost' # The host of the log server (should match to HOST in logger.py)
LOG_SERVER_PORT = 5001 # The port of the log server (should match to PORT in logger.py)

# Define host and port of the API server
API_SERVER_HOST = '172.16.1.98' # The host of the API server
API_SERVER_PORT = 5000 # The port of the API server
API_SERVER_NAME_IN_LOG = 'api-server' # The name of the server in the log messages