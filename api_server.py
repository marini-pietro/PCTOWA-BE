from flask import Flask, request, jsonify
from api_blueprints.blueprints_utils import log
from config import API_SERVER_HOST, API_SERVER_PORT, API_SERVER_DEBUG_MODE, API_SERVER_NAME_IN_LOG
from api_blueprints import *  # Import all the blueprints
import signal, os, importlib

# Create a Flask app
app = Flask(__name__)

# Register the blueprints
blueprints_dir = os.path.dirname(__file__) + '/api_blueprints'
for filename in os.listdir(blueprints_dir):
    if filename.endswith('_bp.py'):  # Look for files ending with '_bp.py'
        module_name = filename[:-3]  # Remove the .py extension
        module = importlib.import_module(f'api_blueprints.{module_name}')
        blueprint = getattr(module, module_name)  # Get the Blueprint object (assumes the object has the same name as the file)
        app.register_blueprint(blueprint, url_prefix=f'/api/{module_name[:-3]}')  # Remove '_bp' for the URL prefix
        print(f"Registered blueprint: {module_name} with prefix /api/{module_name[:-3]}")

# Utility functions
def close_api(signal, frame):  # Parameters are necessary even if not used because it has to match the signal signature
    """
    Gracefully close the API server.
    """
    log(type='info', message='API server shutting down', origin_name=API_SERVER_NAME_IN_LOG, origin_host=API_SERVER_HOST, origin_port=API_SERVER_PORT)
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return 'Server shutting down...'
signal.signal(signal.SIGINT, close_api)  # Bind CTRL+C to close_api function
signal.signal(signal.SIGTERM, close_api)  # Bind SIGTERM to close_api function

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify the server is running.
    """
    return jsonify({"status": "ok"}), 200

# Functions used for testing purposes, should be removed in production
@app.route('/api/endpoints', methods=['GET']) # Only used for testing purposes should be removed in production
def list_endpoints():
    endpoints = []
    for rule in app.url_map.iter_rules():
        endpoints.append({
            "endpoint": rule.endpoint,
            "methods": list(rule.methods),
            "url": rule.rule
        })
    return {"endpoints": endpoints}

@app.route('/api/shutdown', methods=['GET']) # Only used for testing purposes should be removed in production
def shutdown_endpoint():
    close_api(None, None) # Call the close_api function

if __name__ == '__main__':
    app.run(host=API_SERVER_HOST, 
            port=API_SERVER_PORT,
            debug=API_SERVER_DEBUG_MODE)  # Bind to the specific IP address