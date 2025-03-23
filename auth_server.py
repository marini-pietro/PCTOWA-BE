from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, decode_token
from datetime import timedelta
from config import AUTH_SERVER_HOST, AUTH_SERVER_PORT

app = Flask(__name__)

# Configure JWT
app.config['JWT_SECRET_KEY'] = 'your_auth_service_secret_key'  # Use a secure key
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
jwt = JWTManager(app)

@app.route('/auth/login', methods=['POST'])
def login():
    email = request.json.get('email')
    password = request.json.get('password')

    # Validate user credentials (replace with your database logic)
    if email == "test@example.com" and password == "password123":
        access_token = create_access_token(identity={'email': email})
        return jsonify({'access_token': access_token}), 200
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/auth/validate', methods=['POST'])
def validate():
    token = request.json.get('token')
    try:
        decoded_token = decode_token(token)
        return jsonify({'valid': True, 'identity': decoded_token['sub']}), 200
    except Exception as e:
        return jsonify({'valid': False, 'error': str(e)}), 401

if __name__ == '__main__':
    app.run(host=AUTH_SERVER_HOST, 
            port=AUTH_SERVER_PORT, 
            debug=True) # Set debug=False in production