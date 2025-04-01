import json, os, threading
from flask import jsonify
from contextlib import contextmanager
from mysql.connector import pooling as mysql_pooling
from datetime import datetime
from config import DB_HOST, REDACTED_USER, REDACTED_PASSWORD, DB_NAME, \
                   CONNECTION_POOL_SIZE, LOG_SERVER_HOST, LOG_SERVER_PORT, AUTH_SERVER_VALIDATE_URL, STATUS_CODES_EXPLANATIONS
from functools import wraps
from flask import jsonify, request # From Flask import the jsonify function and request object
from requests import post as requests_post # From requests import the post function
from cachetools import TTLCache

# Response related
def make_response(message: dict, status_code: int) -> tuple:
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

# Validation related
metadata_cache = None # Cache the metadata file in memory

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
    global metadata_cache

    # Load metadata into cache if not already loaded
    if metadata_cache is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        metadata_path = os.path.join(base_dir, '..', 'table_metadata.json')
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

    filters_keys = list(data.keys()) if isinstance(data, dict) else []
    invalid_filters = [key for key in filters_keys if key not in available_filters]
    if invalid_filters:
        return {'error': f'Invalid filter(s): {", ".join(invalid_filters)}'}

    return True
            
input_validation_cache = None # Cache the nullable column file in memory

def validate_inputs(table_name: str, inputs: list):
    """
    Validate the inputs against the input validation metadata file.

    params:
        table_name - The name of the table to validate against
        inputs - A list of dictionaries containing column-value pairs to validate

    returns:
        True if validation succeeds, or a string containing the invalid inputs if validation fails.

    raises:
        JSONDecodeError - If the input validation metadata file cannot be parsed
        FileNotFoundError - If the input validation metadata file is not found
        TypeError - If the inputs are not in the expected format
    """
    global input_validation_cache

    # Load input validation metadata into cache if not already loaded
    if input_validation_cache is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        input_validation_path = os.path.join(base_dir, '..', 'input_validation.json')
        try:
            with open(input_validation_path) as input_validation_file:
                input_validation_metadata = json.load(input_validation_file)
                input_validation_cache = input_validation_metadata
        except (json.JSONDecodeError, FileNotFoundError) as e:
            return f'Failed to load input validation metadata: {str(e)}'

    # Validate inputs
    table_metadata = input_validation_cache.get(table_name, [])
    if not isinstance(table_metadata, list) or not all(isinstance(column, dict) for column in table_metadata):
        return f'Invalid metadata structure for table "{table_name}" in input validation metadata'

    invalid_inputs = []
    for input_data in inputs:
        if not isinstance(input_data, dict):
            return 'Invalid input format, expected a list of dictionaries'

        for column, value in input_data.items():
            # Find column metadata
            column_metadata = next((col for col in table_metadata if col["column_name"] == column), None)
            if not column_metadata:
                invalid_inputs.append(f"Unknown column '{column}'")
                continue

            # Check nullability
            if not column_metadata["is_nullable"] and value is None:
                invalid_inputs.append(f"Column '{column}' cannot be null")

            # Check data type
            expected_data_type = column_metadata["data_type"]
            if value is not None:
                if expected_data_type == "int" and not isinstance(value, int):
                    invalid_inputs.append(f"Column '{column}' must be an integer")
                elif expected_data_type == "varchar" and not isinstance(value, str):
                    invalid_inputs.append(f"Column '{column}' must be a string")
                elif expected_data_type == "float" and not isinstance(value, (float, int)):
                    invalid_inputs.append(f"Column '{column}' must be a float")
                elif expected_data_type == "date":
                    try:
                        datetime.strptime(value, "%Y-%m-%d")
                    except ValueError:
                        invalid_inputs.append(f"Column '{column}' must be a valid date in 'YYYY-MM-DD' format")
                elif expected_data_type == "datetime":
                    try:
                        datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        invalid_inputs.append(f"Column '{column}' must be a valid datetime in 'YYYY-MM-DD HH:MM:SS' format")

    if invalid_inputs:
        return f"Validation failed for the following inputs: {', '.join(invalid_inputs)}"

    return True

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
        user=REDACTED_USER,
        password=REDACTED_PASSWORD,
        database=DB_NAME
        )
except Exception as ex:
    print(f"Couldn't access database, see next line for full exception.\n{ex}\n\nhost: {DB_HOST}, dbname: {DB_NAME}, user: {REDACTED_USER}, password: {REDACTED_PASSWORD}")
    exit(1)

def build_query_from_filters(data, table_name, limit=1, offset=0):
    """
    Build a SQL query from filters.
    """
    if not isinstance(data, dict):
        return "SELECT * FROM indirizzi LIMIT %s OFFSET %s", [limit, offset]

    filters = " AND ".join([f"{key} = %s" for key in data.keys()])
    params = list(data.values()) + [limit, offset]
    query = f"SELECT * FROM {table_name} WHERE {filters} LIMIT %s OFFSET %s" if filters else \
            "SELECT * FROM indirizzi LIMIT %s OFFSET %s"
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
        None
    """
    # Use a context manager to ensure the connection is closed after use
    with get_db_connection() as connection:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute(query, params)
            connection.commit()

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
            if response.status_code != 200:
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
            if response.status_code != 200 or not response.json().get('valid'):
                return jsonify({'error': 'Invalid or expired token'}), 401

            is_valid = response.json().get('valid')
            identity = response.json().get('identity')
            token_cache[token] = (is_valid, identity)

        request.user_identity = identity
        return func(*args, **kwargs)
    return wrapper