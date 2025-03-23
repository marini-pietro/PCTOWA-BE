from flask import Flask 
from utils import log, close_log_socket
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

# Define host and port for the API server
API_SERVER_HOST = '172.16.1.98' # The host of the API server
API_SERVER_PORT = 5000 # The port of the API server

# Utility functions
def close_api(signal, frame):  # Parameters are necessary even if not used because it has to match the signal signature
    """
    Gracefully close the API server.
    """
    log('info', 'API server shutting down')
    close_log_socket()  # Close the socket connection to the log server
    exit(0)  # Close the API

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

@app.route('/api/shutdown', methods=['GET']) # Only used for testing purposes should be removed in production (used to remotely close the server while testing)
def shutdown_endpoint():
    close_api()

if __name__ == '__main__':
    app.run(host=API_SERVER_HOST, 
            port=API_SERVER_PORT,
            debug=True)  # Bind to the specific IP address