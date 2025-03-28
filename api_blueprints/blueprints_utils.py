import json
from flask import jsonify
from contextlib import contextmanager
from mysql.connector import pooling as mysql_pooling
from datetime import datetime
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, CONNECTION_POOL_SIZE
from functools import wraps
from flask import jsonify, request # From Flask import the jsonify function and request object
from requests import post as requests_post # From requests import the post function
from config import LOG_SERVER_HOST, LOG_SERVER_PORT, AUTH_SERVER_VALIDATE_URL
from cachetools import TTLCache

def validate_filters(data, table_name):
    """
    Validate the filters in the request data against the metadata file.

    params:
        data - The request data containing the filters in JSON format
        table_name - The name of the table to validate against

    returns:
        A dictionary with an error message if validation fails, or True if validation succeeds.

    raises:
        JSONDecodeError - If the metadata file cannot be parsed
        KeyError - If the table name is not found in the metadata file
        TypeError - If the filters are not in the expected format
        ValueError - If the filters contain invalid values
    """
    with open('../table_metadata.json') as metadata_file:
        try:
            metadata = json.load(metadata_file)
            indirizzi_available_filters = metadata.get(f'{table_name}', [])
            if not isinstance(indirizzi_available_filters, list) or not all(isinstance(item, str) for item in indirizzi_available_filters):
                return {'error': f'invalid {table_name} column values in metadata'}
                
            filters_keys = list(data.keys()) if isinstance(data, dict) else []
            invalid_filters = [key for key in filters_keys if key not in indirizzi_available_filters]
            if invalid_filters:
                return {'error': f'Invalid filter(s): {", ".join(invalid_filters)}'}

            return True

        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            return {'error': 'failed to parse metadata file'}
            
# Data handling related
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

# Database related
# Create a connection pool
try:
    db_pool = mysql_pooling.MySQLConnectionPool(
        pool_name="pctowa_connection_pool",
        pool_size=max(1, CONNECTION_POOL_SIZE),
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
        )
except Exception as ex:
    print(f"Couldn't access database, see next line for full exception.\n{ex}\n\nhost: {DB_HOST}, dbname: {DB_NAME}, user: {DB_USER}, password: {DB_PASSWORD}")
    exit(1)

# Function to get a connection from the pool
@contextmanager
def get_db_connection(): # Make the function a context manager and use a generator to yield the connection
    connection = db_pool.get_connection()
    try:
        yield connection
    finally:
        connection.close()

# Function to clear the connection pool
def clear_db_connection_pool():
    for connection in db_pool._cnx_queue:
        connection.close()
    db_pool._cnx_queue.clear()

# Graceful shutdown handler
def shutdown_handler(signal, frame):
    clear_db_connection_pool()
    print("Database connection pool cleared. Exiting...")
    exit(0)

def fetchone_query(query, params):
    """
    Execute a query on the database and return the result.
    
    params:
        query - The query to execute
        params - The parameters to pass to the query
        
    returns: 
        The result of the query
    """

    with get_db_connection() as connection: # Use a context manager to ensure the connection is closed after use
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()

def fetchall_query(query, params):
    """
    Execute a query on the database and return the result.
    """
    
    with get_db_connection() as connection:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

def execute_query(query, params):
    """
    Execute a query on the database and commit the changes.
    
    params:
        query - The query to execute
        params - The parameters to pass to the query
        
    returns: 
        None
    """
    # Use a context manager to ensure the connection is closed after use
    with get_db_connection() as connection:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute(query, params)
            connection.commit()

# Log server related
def log(type, message, origin_name, origin_host, origin_port) -> None:
    """
    Log a message to the log server via its API.
        
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
            'origin': f"{origin_name} ({origin_host}:{origin_port})",
        }
        
        # Send the log message data to the log server API
        response = requests_post(f"http://{LOG_SERVER_HOST}:{LOG_SERVER_PORT}/log", json=log_data)
        
        # Check if the log server responded with an error
        if response.status_code != 200:
            print(f"Failed to log message: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Failed to send log: {e}")

# Token validation related
# | Create a cache for token validation results with a time-to-live (TTL) of 300 seconds (5 minutes)
token_cache = TTLCache(maxsize=1000, ttl=300)

def jwt_required_endpoint(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Missing token'}), 401

        # Check if the token is already cached
        if token in token_cache:
            is_valid, identity = token_cache[token]
        else:
            # Validate the token with the authentication server
            response = requests_post(AUTH_SERVER_VALIDATE_URL, json={'token': token})
            if response.status_code != 200 or not response.json().get('valid'):
                return jsonify({'error': 'Invalid or expired token'}), 401

            # Cache the validation result
            is_valid = response.json().get('valid')
            identity = response.json().get('identity')
            token_cache[token] = (is_valid, identity)

        # Attach the user identity to the request context
        request.user_identity = identity
        return func(*args, **kwargs)
    return wrapper