from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, decode_token
from datetime import timedelta
from config import AUTH_SERVER_HOST, AUTH_SERVER_PORT, AUTH_SERVER_NAME_IN_LOG, JWT_TOKEN_DURATION
from utils import log, fetchone_query
import secrets

app = Flask(__name__)

# Configure JWT
app.config['JWT_SECRET_KEY'] = secrets.token_hex(32) # Use a secure key (dinamic key, so if jwt are validated, cache and then the server is restarted those same jwt will not be valid with the new key)
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=JWT_TOKEN_DURATION)
jwt = JWTManager(app)

@app.route('/auth/login', methods=['POST'])
def login():
    email = request.json.get('email')
    password = request.json.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    try:
        # Query the database to validate the user's credentials
        query = "SELECT email FROM users WHERE email = %s AND password = %s"
        params = (email, password)  # Use parameterized queries to prevent SQL injection
        user = fetchone_query(query, params)

        if user:
            access_token = create_access_token(identity={'email': email})

            # Log the login operation
            log(type="info",    
                message=f"User {email} logged in",
                origin_name=AUTH_SERVER_NAME_IN_LOG, 
                origin_host=AUTH_SERVER_HOST, 
                origin_port=AUTH_SERVER_PORT)

            return jsonify({'access_token': access_token}), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        # Log the error
        log(type="error",    
            message=f"Error during login: {str(e)}",
            origin_name=AUTH_SERVER_NAME_IN_LOG, 
            origin_host=AUTH_SERVER_HOST, 
            origin_port=AUTH_SERVER_PORT)
        return jsonify({'error': 'An error occurred during login'}), 500

@app.route('/auth/validate', methods=['POST'])
def validate():
    token = request.json.get('token')
    try:
        decoded_token = decode_token(token)
        return jsonify({'valid': True, 'identity': decoded_token['sub']}), 200
    except Exception as e:
        return jsonify({'valid': False, 'error': str(e)}), 401

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify the server is running.
    """
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(host=AUTH_SERVER_HOST, 
            port=AUTH_SERVER_PORT, 
            debug=True) # Set debug=False in production