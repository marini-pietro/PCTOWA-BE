import logging
from flask import Flask, request, jsonify
from os.path import abspath as os_path_abspath
from os.path import dirname as os_path_dirname
from os.path import join as os_path_join
from config import (LOG_SERVER_HOST, LOG_SERVER_PORT, 
                    LOG_SERVER_DEBUG_MODE, LOG_FILE_NAME, 
                    STATUS_CODES)

app = Flask(__name__)

class Logger:
    def __init__(self, log_file, console_level, file_level):
        # Create a logger object
        self.logger = logging.getLogger(name="pctowa_logger")
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

    def log(self, log_type, message, origin="unknown"):
        """
        Log a message with the specified type, message and origin
        """
        log_message = f"[{origin}] {message}"

        log_method = getattr(self.logger, log_type)
        log_method(log_message)

    def close(self):
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)

# Initialize the logger
log_file_path = os_path_join(os_path_dirname(os_path_abspath(__file__)), LOG_FILE_NAME)
logger = Logger(log_file=log_file_path, console_level=logging.INFO, file_level=logging.DEBUG)

@app.route('/log', methods=['POST'])
def log_message():
    """
    Endpoint to log messages.
    Expects a JSON payload with 'type', 'message', and 'origin'.
    """
    data = request.get_json()
    log_type = data.get("type", "info")
    message = data.get("message")
    origin = data.get("origin", "unknown")

    if not message:
        return jsonify({"error": "Message is required"}), STATUS_CODES["bad_request"]

    if log_type not in ["debug", "info", "warning", "error", "critical"]:
        return jsonify({"error": "invalid log type"}), STATUS_CODES["bad_request"]

    try: 
        logger.log(log_type, message, origin)
    except Exception as ex: 
        return jsonify({"error": f"unable to log due to error {ex}"}), STATUS_CODES["internal_error"]

    return jsonify({"status": "success"}), STATUS_CODES["ok"]

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify the server is running.
    """
    return jsonify({"status": "ok"}), STATUS_CODES["ok"]

if __name__ == "__main__":
    try:
        app.run(host=LOG_SERVER_HOST, 
                port=LOG_SERVER_PORT, 
                debug=LOG_SERVER_DEBUG_MODE)
    except KeyboardInterrupt:
        logger.close()