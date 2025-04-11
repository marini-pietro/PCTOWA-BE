from flask import Flask, jsonify
from api_blueprints.blueprints_utils import log
from config import API_SERVER_HOST, API_SERVER_PORT, API_SERVER_DEBUG_MODE, API_SERVER_NAME_IN_LOG, STATUS_CODES
from api_blueprints import *  # Import all the blueprints
from importlib import import_module
import os

# Create a Flask app
app = Flask(__name__)

# Register the blueprints
blueprints_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'api_blueprints')
for filename in os.listdir(blueprints_dir):
    if filename.endswith('_bp.py'):  # Look for files ending with '_bp.py'
        module_name = filename[:-3]  # Remove the .py extension
        module = import_module(f'api_blueprints.{module_name}')
        blueprint = getattr(module, module_name)  # Get the Blueprint object (assumes the object has the same name as the file)
        app.register_blueprint(blueprint, url_prefix=f'/api/')  # Remove '_bp' for the URL prefix
        print(f"Registered blueprint: {module_name} with prefix /api/")

# Utility functions
def close_api(signal, frame):  # Parameters are necessary to match the signal handler signature
    """
    Gracefully close the API server.
    """
    log(type='info', 
        message='API server shutting down', 
        origin_name=API_SERVER_NAME_IN_LOG, 
        origin_host=API_SERVER_HOST, 
        origin_port=API_SERVER_PORT)
    
    # Use the Flask shutdown function directly
    shutdown_func = app.config.get('werkzeug.server.shutdown')
    if shutdown_func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    shutdown_func()
    print("Server shutting down...")

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify the server is running.
    """
    return jsonify({"status": "ok"}), STATUS_CODES["ok"]

# Functions used for testing purposes, should be removed in production
@app.route('/api/endpoints', methods=['GET']) # Only used for testing purposes should be removed in production
def list_endpoints():
    if API_SERVER_DEBUG_MODE == True:
        endpoints = []
        for rule in app.url_map.iter_rules():
            endpoints.append({
                "endpoint": rule.endpoint,
                "methods": list(rule.methods),
                "url": rule.rule
            })
        return jsonify({"endpoints": endpoints}), 200
    else:
        return jsonify({"error": "Feature not available while server is in production mode"}), 403

@app.route('/api/shutdown', methods=['GET']) # Only used for testing purposes should be removed in production
def shutdown_endpoint():
    if API_SERVER_DEBUG_MODE == True:
        close_api(None, None) # Call the close_api function
        return jsonify({"message": "Shutting down server..."}), 200
    else:
        return jsonify({"error": "Feature not available while server is in production mode"}), 403

if __name__ == '__main__':
    app.run(host=API_SERVER_HOST, 
            port=API_SERVER_PORT,
            debug=API_SERVER_DEBUG_MODE)  # Bind to the specific IP address