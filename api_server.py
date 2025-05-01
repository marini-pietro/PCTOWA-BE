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
from flask import Flask, jsonify
from api_blueprints import __all__  # Import all the blueprints
from api_blueprints.blueprints_utils import log
from config import (
    API_SERVER_HOST,
    API_SERVER_PORT,
    API_SERVER_DEBUG_MODE,
    API_SERVER_NAME_IN_LOG,
    STATUS_CODES,
    API_VERSION,
    URL_PREFIX,
)

# Create a Flask app
app = Flask(__name__)

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

        app.register_blueprint(
            blueprint, url_prefix=URL_PREFIX
        )  # Remove '_bp' for the URL prefix
        print(f"Registered blueprint: {module_name} with prefix {URL_PREFIX}")


@app.route(f"/api/{API_VERSION}/health", methods=["GET"])
def health_check():
    """
    Health check endpoint to verify the server is running.
    """
    return jsonify({"status": "ok"}), STATUS_CODES["ok"]


@app.route(f"/api/{API_VERSION}/endpoints", methods=["GET"])
def list_endpoints():
    """
    Endpoint to list all available endpoints in the API.
    Only available in debug mode.
    """
    if API_SERVER_DEBUG_MODE is True:
        endpoints = []
        for rule in app.url_map.iter_rules():
            endpoints.append(
                {
                    "endpoint": rule.endpoint,
                    "methods": list(rule.methods),
                    "url": rule.rule,
                }
            )
        return jsonify({"endpoints": endpoints}), STATUS_CODES["ok"]

    return (
        jsonify(
            {"error": "Feature not available while server is in production mode"}
        ),
        STATUS_CODES["forbidden"],
    )


if __name__ == "__main__":
    app.run(host=API_SERVER_HOST, port=API_SERVER_PORT, debug=API_SERVER_DEBUG_MODE)
    log(
        log_type="info",
        message="API server started",
        origin_name=API_SERVER_NAME_IN_LOG,
        origin_host=API_SERVER_HOST,
        message_id="UserAction",
        structured_data=f"[host: {API_SERVER_HOST}, port: {API_SERVER_PORT}]",
    )
