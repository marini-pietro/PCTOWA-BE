from flask import Flask, request, jsonify
from config import LOG_SERVER_HOST, LOG_SERVER_PORT, LOG_SERVER_DEBUG_MODE
import logging

app = Flask(__name__)

class Logger:
    def __init__(self, log_file="PCTO_webapp_backend.log", console_level=logging.INFO, file_level=logging.DEBUG):
        # Create a logger object
        self.logger = logging.getLogger("api_logger")
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

    def log(self, log_type, message, origin="unknown") -> None:
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
logger = Logger()

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
        return jsonify({"error": "Message is required"}), 400

    if log_type not in ["debug", "info", "warning", "error", "critical"]:
        return jsonify({"error": "invalid log type"}), 400

    try: 
        logger.log(log_type, message, origin)
    except Exception as ex: 
        return jsonify({"error": f"unable to log due to error {ex}"}), 500

    return jsonify({"status": "success"}), 200

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify the server is running.
    """
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    try:
        app.run(host=LOG_SERVER_HOST, port=LOG_SERVER_PORT, debug=LOG_SERVER_DEBUG_MODE)
    except KeyboardInterrupt:
        logger.close()