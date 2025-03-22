import requests
from subprocess import Popen as subprocess_popen
from os import name as os_name
from os import system as cmd
from time import sleep

# Define API host and port to test
HOST = 'http://localhost'
PORT = 12345
API_BASE_PATH = HOST + '/api'

# Clear the terminal
cmd('cls' if 'nt' in os_name else 'clear')

# Start api server
print("Starting API server...")
try:
    # Start the server as a subprocess
    if os_name == 'nt':  # Windows
        subprocess_popen(["python", "api.py"], shell=True)
    else:  # Linux/Unix
        subprocess_popen(["python", "api.py"])
    print("API server started, testing will begin shortly...")
except Exception as ex:
    print(f"Error starting API server: {ex}\nExiting...")
    exit(1)

# Retrieve and simplify API endpoints
try:
    response = requests.get(f"{API_BASE_PATH}/endpoint")
    response.raise_for_status()
    API_ENDPOINTS = [
        {
            "name": endpoint['url'].rstrip('/').split('/')[-1],
            "methods": endpoint['methods']
        }
        for endpoint in response.json()
    ]
except requests.RequestException as ex:
    print(f"Error retrieving endpoints: {ex}")
    exit(1)

# Expected response status codes
EXPECTED_STATUS_CODES = {
    'GET': 200,
    'POST': 201,
    'PUT': 200,
    'DELETE': 204
}

# Expected response content types
EXPECTED_CONTENT_TYPES = {
    'GET': 'application/json',
    'POST': 'application/json',
    'PUT': 'application/json',
    'DELETE': 'application/json'
}

# Expected response data TODO - Update this with the expected response data for each endpoint
EXPECTED_RESPONSE_DATA = {
    'GET': {},
    'POST': {},
    'PUT': {},
    'DELETE': {}
}

# Begin testing
total_endpoints = len(API_ENDPOINTS)
for i, endpoint in enumerate(API_ENDPOINTS, start=1):
    endpoint_name = endpoint['name']
    endpoint_methods = endpoint['methods']
    test_passed = True

    # Update progress bar
    progress = f"Testing endpoint {i}/{total_endpoints}: {endpoint_name} [{'=' * i}{' ' * (total_endpoints - i)}]"
    print(progress, end='\r')

    for method in endpoint_methods:
        try:
            # Make the request
            response = requests.request(method, f"{API_BASE_PATH}/{endpoint_name}")
            response.raise_for_status()

            # Validate response
            if response.status_code != EXPECTED_STATUS_CODES[method]:
                print(f"[{method}] {endpoint_name}: Unexpected status code {response.status_code}")
                test_passed = False

            if response.headers.get('Content-Type') != EXPECTED_CONTENT_TYPES[method]:
                print(f"[{method}] {endpoint_name}: Unexpected content type {response.headers.get('Content-Type')}")
                test_passed = False

            if response.json() != EXPECTED_RESPONSE_DATA[method]:
                print(f"[{method}] {endpoint_name}: Unexpected response data {response.json()}")
                test_passed = False

        except requests.RequestException as ex:
            print(f"[{method}] {endpoint_name}: Request failed - {ex}")
            test_passed = False

    # Print test result for the endpoint
    if test_passed:
        print(f"\nEndpoint {endpoint_name} passed all tests")
    else:
        print(f"\nEndpoint {endpoint_name} failed one or more tests")

    # Simulate delay for better visualization (optional)
    sleep(0.1)

print("\nTesting complete, closing API server...")
requests.get(f"{API_BASE_PATH}/shutdown")