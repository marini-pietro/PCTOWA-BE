from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta
from api_blueprints.blueprints_utils import log, fetchone_query
from config import (AUTH_SERVER_HOST, AUTH_SERVER_PORT, 
                    AUTH_SERVER_NAME_IN_LOG, AUTH_SERVER_DEBUG_MODE, 
                    JWT_TOKEN_DURATION, JWT_SECRET_KEY,
                    STATUS_CODES)

app = Flask(__name__)

# Check JWT secret key length
password_bits_length = len(JWT_SECRET_KEY.encode('utf-8')) * 8
if password_bits_length < 256:
    raise RuntimeWarning("jwt secret key too short")

# Configure JWT
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY # Use a secure key (ideally at least 256 bits)
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=JWT_TOKEN_DURATION)
jwt = JWTManager(app)

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'missing email or password'}), STATUS_CODES["bad_request"]

    try:
        # Query the database to validate the user's credentials
        query = "SELECT emailUtente, password, ruolo FROM utenti WHERE emailUtente = %s AND password = %s"
        user = fetchone_query(query, (email, password))

        if user:
            access_token = create_access_token(identity={'email': email,
                                                         'role': user['ruolo']})

            # Log the login operation
            log(type="info",    
                message=f"User {email} logged in",
                origin_name=AUTH_SERVER_NAME_IN_LOG, 
                origin_host=AUTH_SERVER_HOST, 
                origin_port=AUTH_SERVER_PORT)

            return jsonify({'access_token': access_token}), STATUS_CODES["ok"]
        else:
            # Log the failed login attempt
            log(type="warning",    
                message=f"Failed login attempt for {email} with password {password}",
                origin_name=AUTH_SERVER_NAME_IN_LOG, 
                origin_host=AUTH_SERVER_HOST, 
                origin_port=AUTH_SERVER_PORT)
            
            # Return unauthorized status
            return jsonify({'error': 'Invalid credentials'}), STATUS_CODES["unauthorized"]
    except Exception as e:
        log(type="error",    
            message=f"Error during login: {str(e)}",
            origin_name=AUTH_SERVER_NAME_IN_LOG, 
            origin_host=AUTH_SERVER_HOST, 
            origin_port=AUTH_SERVER_PORT)
        return jsonify({'error': 'An error occurred during login'}), STATUS_CODES["internal_error"]

@app.route('/auth/validate', methods=['POST'])
@jwt_required()
def validate():
    identity = get_jwt_identity()
    return jsonify({'valid': True, 'identity': identity}), STATUS_CODES["ok"]

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify the server is running.
    """
    return jsonify({"status": "ok"}), STATUS_CODES["ok"]

if __name__ == '__main__':
    app.run(host=AUTH_SERVER_HOST, 
            port=AUTH_SERVER_PORT, 
            debug=AUTH_SERVER_DEBUG_MODE) # Set debug=False in production