"""
API server for the application.
This server handles incoming requests and routes them to the appropriate blueprints.
It also provides a health check endpoint and a shutdown endpoint.
"""

from os import listdir as os_listdir
from os.path import join as os_path_join
from os.path import dirname as os_path_dirname
from os.path import abspath as os_path_abspath
from importlib import import_module
from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager
from api_blueprints import __all__  # Import all the blueprints
from api_blueprints.blueprints_utils import log, is_rate_limited
from config import (
    API_SERVER_HOST,
    API_SERVER_PORT,
    API_SERVER_DEBUG_MODE,
    API_SERVER_NAME_IN_LOG,
    STATUS_CODES,
    API_VERSION,
    URL_PREFIX,
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    JWT_QUERY_STRING_NAME,
    JWT_ACCESS_COOKIE_NAME,
    JWT_REFRESH_COOKIE_NAME,
    JWT_JSON_KEY,
    JWT_REFRESH_JSON_KEY,
    JWT_TOKEN_LOCATION,
    JWT_REFRESH_TOKEN_EXPIRES,
)

# Create a Flask app
main_api = Flask(__name__)

# Configure JWT validation settings
main_api.config["JWT_SECRET_KEY"] = (
    JWT_SECRET_KEY  # Same secret key as the auth microservice
)
main_api.config["JWT_ALGORITHM"] = JWT_ALGORITHM  # Same algorithm as the auth microservice
main_api.config["JWT_TOKEN_LOCATION"] = JWT_TOKEN_LOCATION  # Where to look for tokens
main_api.config["JWT_QUERY_STRING_NAME"] = JWT_QUERY_STRING_NAME  # Custom query string name
main_api.config["JWT_ACCESS_COOKIE_NAME"] = (
    JWT_ACCESS_COOKIE_NAME  # Custom access cookie name
)
main_api.config["JWT_REFRESH_COOKIE_NAME"] = (
    JWT_REFRESH_COOKIE_NAME  # Custom refresh cookie name
)
main_api.config["JWT_JSON_KEY"] = JWT_JSON_KEY  # Custom JSON key for access tokens
main_api.config["JWT_REFRESH_JSON_KEY"] = (
    JWT_REFRESH_JSON_KEY  # Custom JSON key for refresh tokens
)
main_api.config["JWT_REFRESH_TOKEN_EXPIRES"] = (
    JWT_REFRESH_TOKEN_EXPIRES  # Refresh token valid duration
)

# Initialize JWTManager for validation only
jwt = JWTManager(main_api)

# Register the blueprints
blueprints_dir: str = os_path_join(
    os_path_dirname(os_path_abspath(__file__)), "api_blueprints"
)
for filename in os_listdir(blueprints_dir):
    if filename.endswith("_bp.py"):  # Look for files ending with '_bp.py'

        # Import the module dynamically
        module_name: str = filename[:-3]  # Remove the .py extension
        module = import_module(f"api_blueprints.{module_name}")

        # Get the Blueprint object (assumes the object has the same name as the file)
        blueprint = getattr(module, module_name)

        main_api.register_blueprint(
            blueprint, url_prefix=URL_PREFIX
        )  # Remove '_bp' for the URL prefix
        print(f"Registered blueprint: {module_name} with prefix {URL_PREFIX}")

@main_api.before_request
def enforce_rate_limit():
    """
    Enforce rate limiting for all incoming requests.
    """
    client_ip = request.remote_addr
    if is_rate_limited(client_ip):
        return jsonify({"error": "Rate limit exceeded"}), STATUS_CODES["too_many_requests"]

# Handle unauthorized access (missing token)
@jwt.unauthorized_loader
def custom_unauthorized_response(callback):
    return jsonify({"error": "Missing or invalid token"}), STATUS_CODES["unauthorized"]


# Handle invalid tokens
@jwt.invalid_token_loader
def custom_invalid_token_response(callback):
    log(
        log_type="error",
        message=f"api reached with invalid token, callback: {callback}",
        origin_name=API_SERVER_NAME_IN_LOG,
        origin_host=API_SERVER_HOST,
        message_id="UserAction",
        structured_data=f"[host: {API_SERVER_HOST}, port: {API_SERVER_PORT}]",
    )
    return jsonify({"error": "Invalid token"}), STATUS_CODES["unprocessable_entity"]


# Handle expired tokens
@jwt.expired_token_loader
def custom_expired_token_response(jwt_header, jwt_payload):
    return jsonify({"error": "Token has expired"}), STATUS_CODES["unauthorized"]


# Handle revoked tokens (if applicable)
@jwt.revoked_token_loader
def custom_revoked_token_response(jwt_header, jwt_payload):
    return jsonify({"error": "Token has been revoked"}), STATUS_CODES["unauthorized"]


@main_api.route(f"/api/{API_VERSION}/health", methods=["GET"])
def health_check():
    """
    Health check endpoint to verify the server is running.
    """
    return jsonify({"status": "ok"}), STATUS_CODES["ok"]

if __name__ == "__main__":
    main_api.run(host=API_SERVER_HOST, port=API_SERVER_PORT, debug=API_SERVER_DEBUG_MODE)
    log(
        log_type="info",
        message="API server started",
        origin_name=API_SERVER_NAME_IN_LOG,
        origin_host=API_SERVER_HOST,
        message_id="UserAction",
        structured_data=f"[host: {API_SERVER_HOST}, port: {API_SERVER_PORT}]",
    )
