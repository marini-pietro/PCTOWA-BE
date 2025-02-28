from flask import Flask, jsonify, request
import sqlite3

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

app = Flask(__name__)
conn = get_db_connection()

@app.route('/user_login', methods=['GET'])
def user_login():
    username = request.args.get('username')
    password = request.args.get('password')

    users = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    return jsonify([dict(user) for user in users])

if __name__ == '__main__':
    app.run(debug=True)