from flask import Flask, jsonify, request
import mysql.connector

conn = mysql.connector.connect(
        host='172.16.1.98',
        user='pctowa',
        password='pctowa2025',
        database='pctowa'
        )
app = Flask(__name__)

# User login related
@app.route('/user_login', methods=['GET'])
def user_login():
    username = request.args.get('username')
    password = request.args.get('password')

    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
    if cursor.rowcount == 1: 
        return jsonify({"outcome": "user with provided credentials exists"})
    else: 
        return jsonify({"outcome": "error, user with provided credentials already exists"})
    
@app.route('/user_register', methods=['GET'])
def user_register():
    username = request.args.get('username')
    password = request.args.get('password')
    type = request.args.get('type')

    cursor = conn.cursor(dictionary=True)
    
    # Find out if user already exists
    cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
    if cursor.rowcount != 1:
        return jsonify({"outcome": "error, user with provided credentials already exists"}) # If it does return error data
    else:
        # If not 
        cursor.execute('INSERT INTO users VALUES (%s, %s, %s)', (username, password, type))
        return jsonify({"outcome": "user successfully created"})
    
def close_api():
    conn.close()
    exit

if __name__ == '__main__':
    app.run(debug=True) # Debug uguale a True per facilitare lo sviluppo andrebbe messo a false in produzione