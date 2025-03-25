import subprocess
import requests
import time
from config import *

def wait_for_server(host, port, retries=5, delay=1):
    """
    Wait for a server to become available by polling its health endpoint.
    
    :param host: Server host
    :param port: Server port
    :param retries: Number of retries before giving up
    :param delay: Delay (in seconds) between retries
    :return: True if the server is available, False otherwise
    """
    url = f"http://{host}:{port}/health"
    for _ in range(retries):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return True
        except requests.ConnectionError:
            pass
        time.sleep(delay)
    return False

# Start the log server
subprocess.Popen(["python", "log_server.py"])
if not wait_for_server(LOG_SERVER_HOST, LOG_SERVER_PORT):
    print("Log server is not running properly, continuing to run without it.\n")

# Start the authentication server
subprocess.Popen(["python", "auth_server.py"])
if not wait_for_server(AUTH_SERVER_HOST, AUTH_SERVER_PORT):
    print("Auth server is not running properly")
    exit(1)

# Start the API server
subprocess.Popen(["python", "api_server.py"])
if not wait_for_server(API_SERVER_HOST, API_SERVER_PORT):
    print("API server is not running properly")
    exit(1)

print("All servers are running successfully!")