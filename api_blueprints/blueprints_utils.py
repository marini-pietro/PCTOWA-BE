import threading, json, os
from flask import jsonify, make_response, request
from contextlib import contextmanager
from mysql.connector import pooling as mysql_pooling
from datetime import datetime
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, CONNECTION_POOL_SIZE, LOG_SERVER_HOST, LOG_SERVER_PORT, AUTH_SERVER_VALIDATE_URL, STATUS_CODES_EXPLANATIONS, STATUS_CODES
from functools import wraps
from requests import post as requests_post # From requests import the post function
from cachetools import TTLCache
from typing import Dict, Any

# Casting related
input_validation_cache = None

def perform_casting_operations(data: Dict[str, str]) -> Dict[str, Any]:
    """
    Given a dictionary of data it compares the data type of the value of a key in data to the data type written in the input_validation json and if they are different it performs the necessary casting and returns the dictionary with the correct types.
    If a value that cannot be null is passed as null in the data dictionary it returns False
    """
    global input_validation_cache

    # Load input validation metadata into cache if not already loaded
    if input_validation_cache is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        metadata_path = os.path.join(base_dir, '..', 'input_validation.json')
        if not os.path.exists(metadata_path): # Check if the file exists
            # If the file doesn't exist, generate it using the input_validation_generator.py script
            os.system("python3 input_validation_generator.py")
        try:
            with open(metadata_path) as metadata_file:
                input_validation_cache = json.load(metadata_file)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            return {'error': f'Failed to load metadata: {str(e)}'}
        
    # Validate input data against metadata
    for key, value in data.items():
        # Check if the key exists in the metadata
        if key in input_validation_cache:
            expected_type = input_validation_cache[key].get('type')
            is_nullable = input_validation_cache[key].get('nullable', False)

            # Perform casting based on expected type
            if expected_type == 'int':
                try:
                    data[key] = int(value)
                except (ValueError, TypeError):
                    if not is_nullable:
                        return False
                    data[key] = None
            elif expected_type == 'str' or expected_type == 'varchar' or expected_type == 'char':
                data[key] = str(value)
            elif expected_type == 'bool':
                if value.lower() in ['true', '1', 'yes']:
                    data[key] = True
                elif value.lower() in ['false', '0', 'no']:
                    data[key] = False
                else:
                    if not is_nullable:
                        return False
                    data[key] = None
            elif expected_type == 'datetime':
                try:
                    data[key] = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                except (ValueError, TypeError):
                    if not is_nullable:
                        return False
                    data[key] = None
            elif expected_type == 'date':
                try:
                    data[key] = datetime.strptime(value, '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    if not is_nullable:
                        return False
                    data[key] = None
            elif expected_type == 'time':
                try:
                    data[key] = datetime.strptime(value, '%H:%M').time()
                except (ValueError, TypeError):
                    if not is_nullable:
                        return False
                    data[key] = None

# Authorization related
def check_authorization(allowed_user_types):
    """
    Decorator to check if the user's type is in the allowed list.
    
    params:
        allowed_user_types: list[str] - List of user types that are permitted to execute the function.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check if user_type exists in the request and is allowed
            user_type = getattr(request, 'user_type', None)
            if user_type not in allowed_user_types:
                return create_response(
                    message={'outcome': 'not permitted'}, 
                    status_code=STATUS_CODES["forbidden"]
                )
            # Proceed with the original function
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Validation related
def validate_filters(fields: list[str], table_name: str):
    """
    Checks if the provided filters are actually column names in the database..

    params:
        fields - The filters to validate
        table_name - The name of the table to validate against

    returns:
        A dictionary with an error message if validation fails, or True if validation succeeds.

    raises:
        JSONDecodeError - If the metadata file cannot be parsed
        KeyError - If the table name is not found in the metadata file
        TypeError - If the filters are not in the expected format
        ValueError - If the filters contain invalid values
    """
    global metadata_cache

    # Load metadata into cache if not already loaded
    if metadata_cache is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        metadata_path = os.path.join(base_dir, '..', 'table_metadata.json')
        if not os.path.exists(metadata_path):
            os.system("python3 valid_filters_generator.py")
        try:
            with open(metadata_path) as metadata_file:
                metadata = json.load(metadata_file)
                # Convert list to dictionary if necessary
                if isinstance(metadata, list):
                    metadata = {key: value for item in metadata for key, value in item.items()}
                metadata_cache = metadata
        except (json.JSONDecodeError, FileNotFoundError) as e:
            return {'error': f'Failed to load metadata: {str(e)}'}

    # Validate filters
    available_filters = metadata_cache.get(f'{table_name}', [])
    if not isinstance(available_filters, list) or not all(isinstance(item, str) for item in available_filters):
        return {'error': f'invalid {table_name} column values in metadata'}

    invalid_filters = [key for key in fields if key not in available_filters]
    if invalid_filters:
        return {'error': f'Invalid filter(s): {", ".join(invalid_filters)}'}

    return True

# Response related
def create_response(message: dict, status_code: int) -> tuple:
    """
    Create a response with a message and status code.

    params:
        message - The message to include in the response
        status_code - The HTTP status code to return

    returns:
        A tuple containing the response message and status code

    raises:
        TypeError - If the message is not a dictionary or the status code is not an integer
    """

    if not isinstance(message, dict):
        raise TypeError("Message must be a dictionary")

    message = f"{message}\n{STATUS_CODES_EXPLANATIONS.get(status_code, 'Unknown status code')}"

    return make_response(jsonify(message), status_code)

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

def build_select_query_from_filters(data, table_name, limit=1, offset=0):
    """
    Build a SQL query from filters.
    Does not support complex queries with joins or subqueries.

    params:
        data - The filters to apply to the query
        table_name - The name of the table to query
        limit - The maximum number of results to return
        offset - The offset for pagination
    
    returns:
        A tuple containing the query and the parameters to pass to the query

    raises:
        None
    """

    filters = " AND ".join([f"{key} = %s" for key in data.keys()])
    params = list(data.values()) + [limit, offset]
    query = f"SELECT * FROM {table_name} WHERE {filters} LIMIT %s OFFSET %s"
    return query, params

def build_update_query_from_filters(data, table_name, id_column):
    """
    Build a SQL update query from filters.
    
    params:
        data - The filters to apply to the query
        table_name - The name of the table to query
        id_column - The name of the ID column to use for the update
    
    returns:
        A tuple containing the query and the parameters to pass to the query

    raises:
        None
    """

    filters = ", ".join([f"{key} = %s" for key in data.keys()])
    params = list(data.values())
    query = f"UPDATE {table_name} SET {filters} WHERE {id_column} = %s"
    return query, params

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
        The ID of the last inserted row, if applicable
    """
    # Use a context manager to ensure the connection is closed after use
    with get_db_connection() as connection:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute(query, params)
            connection.commit()
            return cursor.lastrowid

def execute_batch_queries(queries_with_params):
    """
    Execute multiple queries in a single transaction.
    
    params:
        queries_with_params - A list of tuples (query, params)
        
    returns:
        None
    """
    with get_db_connection() as connection:
        with connection.cursor(dictionary=True) as cursor:
            for query, params in queries_with_params:
                cursor.execute(query, params)
            connection.commit()

# Log server related
def log(type, message, origin_name, origin_host, origin_port) -> None:
    """
    Asynchronously logs a message to the log server via its API.
        
    params:
        type - The type of the log message
        message - The message to log
        
    returns: 
        None
    """
    def send_log():
        try:
            log_data = {
                'type': type,
                'message': message,
                'origin': f"{origin_name} ({origin_host}:{origin_port})",
            }
            response = requests_post(f"http://{LOG_SERVER_HOST}:{LOG_SERVER_PORT}/log", json=log_data)
            if response.status_code != STATUS_CODES["ok"]:
                print(f"Failed to log message: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Failed to send log: {e}")

    threading.Thread(target=send_log, daemon=True).start()

# Token validation related
# | Create a cache for token validation results with a time-to-live (TTL) of 300 seconds (5 minutes)
token_cache = TTLCache(maxsize=1000, ttl=300)

def jwt_required_endpoint(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Missing token'}), 401

        # Check token cache
        cached_result = token_cache.get(token)
        if cached_result:
            is_valid, identity = cached_result
        else:
            # Validate token with auth server
            response = requests_post(AUTH_SERVER_VALIDATE_URL, json={'token': token})
            if response.status_code != STATUS_CODES["ok"] or not response.json().get('valid'):
                return jsonify({'error': 'Invalid or expired token'}), 401

            is_valid = response.json().get('valid')
            identity = response.json().get('identity')
            token_cache[token] = (is_valid, identity)

        request.user_identity = identity
        return func(*args, **kwargs)
    return wrapper