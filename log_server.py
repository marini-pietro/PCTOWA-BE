import socket
import re
import logging
import time
import threading
from collections import defaultdict, deque
from threading import Thread, Lock
from os.path import abspath as os_path_abspath
from os.path import dirname as os_path_dirname
from os.path import join as os_path_join
from config import (LOG_SERVER_HOST, LOG_SERVER_PORT, 
                    LOG_FILE_NAME, LOGGER_NAME,
                    RATE_LIMIT, TIME_WINDOW,
                    DELAYED_LOGS_QUEUE_SIZE)

# Define the logger class
class Logger:
    def __init__(self, log_file, console_level, file_level):
        # Create a logger object
        self.logger: Logger = logging.getLogger(name=LOGGER_NAME)
        self.logger.setLevel(logging.DEBUG)

        # Create a console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_level)

        # Create a file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(file_level)

        # Create formatter objects and set the format of the log messages
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        # Add handlers to the logger
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    # Function to log messages with different levels (automatically retrieves the right function based on the log type parameter)
    # The log_type parameter should be one of the logging levels: debug, info, warning, error, critical
    def log(self, log_type, message, origin):
        """
        Log a message with the specified type, message and origin
        """

        log_method = getattr(self.logger, log_type)
        log_method(f"[{origin}] {message}")

    # Function to close all handlers
    def close(self):
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)

# Generate the log file path so that it is in the same directory as this script
log_file_path: str = os_path_join(os_path_dirname(os_path_abspath(__file__)), LOG_FILE_NAME)

# Initialize the logger
logger = Logger(log_file=log_file_path, console_level=logging.INFO, file_level=logging.DEBUG)

# Add a shutdown flag
shutdown_flag = threading.Event()

def start_syslog_server(host, port):
    """
    Start a syslog server that listens for messages over UDP.
    """
    syslog_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    syslog_socket.bind((host, port))
    print(f"Syslog server listening on {host}:{port}")

    try:
        while not shutdown_flag.is_set():  # Check the shutdown flag
            syslog_socket.settimeout(1.0)  # Set a timeout to periodically check the flag
            try:
                data, addr = syslog_socket.recvfrom(1024)
                message = data.decode('utf-8')
                process_syslog_message(message, addr)
            except socket.timeout:
                continue  # Continue the loop if no data is received
    except KeyboardInterrupt:
        print("Shutting down syslog server...")
    finally:
        shutdown_flag.set()  # Signal the background thread to stop
        syslog_socket.close()
        logger.close()

# Compile the RFC 5424 syslog message regex pattern once
SYSLOG_PATTERN = re.compile(
    r"<(\d+)>"                  # PRI
    r"(\d{1,2}) "               # VERSION
    r"(\S+) "                   # TIMESTAMP
    r"(\S+) "                   # HOSTNAME
    r"(\S+) "                   # APP-NAME
    r"(\S+) "                   # PROCID
    r"(\S+) "                   # MSGID
    r"(\[.*?\]|-) "             # STRUCTURED-DATA
    r"(.*)"                     # MSG
)

# Dictionary to track message counts and timestamps per source
message_counts = defaultdict(lambda: {"count": 0, "timestamp": time.time()})

# Queue to store delayed logs
delayed_logs = deque(maxlen=DELAYED_LOGS_QUEUE_SIZE)  # Limit the size of the queue to avoid memory issues
queue_lock = Lock()  # Lock to ensure thread-safe access to the queue

def process_syslog_message(message, addr):
    """
    Process and log a syslog message according to RFC 5424 with rate limiting.
    """
    source_ip = addr[0]
    current_time = time.time()

    # Check and reset the count if the time window has passed
    if current_time - message_counts[source_ip]["timestamp"] > TIME_WINDOW:
        message_counts[source_ip] = {"count": 0, "timestamp": current_time}

    # Increment the message count for the source
    message_counts[source_ip]["count"] += 1

    # Enforce rate limit
    if message_counts[source_ip]["count"] > RATE_LIMIT:
        # Add the log to the delayed queue instead of dropping it
        with queue_lock:
            delayed_logs.append((message, addr))
        logger.log(
            "warning",
            f"Rate limit exceeded for {source_ip}. Delaying message: {message}",
            f"Syslog-{source_ip}"
        )
        return  # Do not process the message immediately

    # Process the syslog message as usual
    _process_message(message, addr)

def _process_message(message, addr):
    """
    Helper function to process a syslog message.
    """
    match = SYSLOG_PATTERN.match(message)
    if match:
        # Extract fields from the syslog message
        priority = int(match.group(1))
        version = match.group(2)
        timestamp = match.group(3)
        hostname = match.group(4)
        app_name = match.group(5)
        proc_id = match.group(6)
        msg_id = match.group(7)
        structured_data = match.group(8)
        msg_content = match.group(9)

        # Map priority to log level
        log_level = {
            0: "critical",
            1: "alert",
            2: "critical",
            3: "error",
            4: "warning",
            5: "notice",
            6: "info",
            7: "debug",
        }.get(priority % 8, "info")  # Default to "info" if unknown

        # Log the message with detailed information
        logger.log(
            log_type=log_level,
            message=f"{timestamp} {hostname} {app_name} {proc_id} {msg_id} {structured_data} {msg_content}",
            origin=f"sourceIP-{addr[0]}"
        )
    else:
        # Log a warning for invalid syslog messages
        logger.log("warning", f"Invalid syslog message: {message}", f"Syslog-{addr[0]}")

def process_delayed_logs():
    """
    Periodically process delayed logs from the queue.
    """
    while not shutdown_flag.is_set():  # Check the shutdown flag
        with queue_lock:
            if delayed_logs:
                message, addr = delayed_logs.popleft()
                _process_message(message, addr)
        time.sleep(0.1)  # Adjust the sleep interval as needed

# Start a background thread to process delayed logs
Thread(target=process_delayed_logs, daemon=True).start()

if __name__ == "__main__":
    start_syslog_server(LOG_SERVER_HOST, LOG_SERVER_PORT)