from functools import wraps
from flask import jsonify, request # From Flask import the jsonify function and request object
from requests import post as requests_post # From requests import the post function
from json import dumps as json_dumps # From json import the dumps function
from config import *
import mysql.connector, socket
from datetime import datetime

# Create a connection pool
CONNECTION_POOL_SIZE = 10 # The maximum number of connections in the pool
db_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="pctowa_connection_pool",
    pool_size=CONNECTION_POOL_SIZE,
    host="localhost",
    user="pctowa",
    password="pctowa2025",
    database="pctowa"
)

# Function to get a connection from the pool
def get_db_connection():
    return db_pool.get_connection()

# Function to clear the connection pool
def clear_db_connection_pool():
    # Close all connections in the connection pool
    for connection in db_pool._cnx_queue:
        connection.close()
    db_pool._cnx_queue.clear()

# Create a socket object at the start of the program
log_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
log_socket.connect((LOG_SERVER_HOST, LOG_SERVER_PORT))

def log(type, message) -> None:
    """
    Log a message to the log server.
        
    params:
        type - The type of the log message
        message - The message to log
        
    returns: 
        None
    """
    try:
        # Create a dictionary with the log message data
        log_data = {
            'type': type,
            'message': message,
            'origin': f"{API_SERVER_NAME_IN_LOG} ({API_SERVER_HOST}:{API_SERVER_PORT})",
        }
            
        # Send the log message data to the log server
        log_socket.sendall(json_dumps(log_data).encode('utf-8'))
    except Exception as e:
        print(f"Failed to send log: {e}")

def close_log_socket():
    """
    Close the socket connection to the log server.
        
    returns: 
        None
    """
    log_socket.close()

def parse_time_string(time_string) -> datetime:
    """
    Parse a time string in the format HH:MM and return a datetime object.
    
    params:
        time_string - The time string to parse
    
    returns: 
        A datetime object if the string is in the correct format, None otherwise

    """

    try: return datetime.strptime(time_string, '%H:%M').time()
    except ValueError: return None

def parse_date_string(date_string) -> datetime:
    """
    Parse a date string in the format YYYY-MM-DD and return a datetime object.
    
    params:
        date_string - The date string to parse
    
    returns: 
        A datetime object if the string is in the correct format, None otherwise

    """

    try: return datetime.strptime(date_string, '%Y-%m-%d').date()
    except ValueError: return None

def jwt_required_endpoint(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Missing token'}), 401

        # Validate the token with the authentication server
        response = requests_post(AUTH_SERVER_VALIDATE_URL, json={'token': token})
        if response.status_code != 200 or not response.json().get('valid'):
            return jsonify({'error': 'Invalid or expired token'}), 401

        # Attach the user identity to the request context
        request.user_identity = response.json().get('identity')
        return func(*args, **kwargs)
    return wrapper

def fetchone_query(query, params):
    """
    Execute a query on the database and return the result.
    
    params:
        query - The query to execute
        params - The parameters to pass to the query
        
    returns: 
        The result of the query
    """
    with get_db_connection().cursor(dictionary=True) as cursor: # Use a context manager to automatically close the cursor
        cursor.execute(query, params)
        return cursor.fetchone()

def fetchall_query(query, params):
    """
    Execute a query on the database and return the result.
    
    params:
        query - The query to execute
        params - The parameters to pass to the query
        
    returns: 
        The result of the query
    """

    with get_db_connection().cursor(dictionary=True) as cursor: # Use a context manager to automatically close the cursor
        cursor.execute(query, params)
        return cursor.fetchall()

def execute_query(query, params):
    """
    Execute a query on the database and return the result.
    
    params:
        query - The query to execute
        params - The parameters to pass to the query
        
    returns: 
        The result of the query
    """
    cursor = get_db_connection().cursor(dictionary=True)
    cursor.execute(query, params)
    get_db_connection().commit()