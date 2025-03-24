from flask import Flask, request
from utils import log
from config import API_SERVER_HOST, API_SERVER_PORT, API_SERVER_DEBUG_MODE, API_SERVER_NAME_IN_LOG
from api_blueprints import *  # Import all the blueprints
import signal

# Create a Flask app
app = Flask(__name__)

# Register the blueprints
app.register_blueprint(address_bp, url_prefix='/api/address')
app.register_blueprint(class_bp, url_prefix='/api/class')
app.register_blueprint(company_bp, url_prefix='/api/company')
app.register_blueprint(contact_bp, url_prefix='/api/contact')
app.register_blueprint(sector_bp, url_prefix='/api/sector')
app.register_blueprint(student_bp, url_prefix='/api/student')
app.register_blueprint(subject_bp, url_prefix='/api/subject')
app.register_blueprint(turn_bp, url_prefix='/api/turn')
app.register_blueprint(tutor_bp, url_prefix='/api/tutor')
app.register_blueprint(user_bp, url_prefix='/api/user')

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