import logging
from json import loads as json_loads, JSONDecodeError
from socketserver import BaseRequestHandler, TCPServer

class Logger:
    def __init__(self, log_file="PCTO_Webapp_backend.log", console_level=logging.INFO, file_level=logging.DEBUG):
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

    def log(self, log_type, message, origin="unknown"):
        """
        Log a message with the specified type, message and origin
        
        params
            log_type: The type of the log message (e.g. info, error, warning)
            message: The log message
            origin: The origin of the log message

        returns:
            None

        raises:
            None
        """	
        log_message = f"[{origin}] {message}"
        log_type = log_type.lower()
        
        if log_type not in ["debug", "info", "warning", "error", "critical"]:
            return self.logger.error(f"Origin {origin} tried to log [{message}] with invalid log type [{log_type}]")
        
        log_method = getattr(self.logger, log_type)
        log_method(log_message)

    def close(self):
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)

class LogRequestHandler(BaseRequestHandler):
    def __init__(self, *args, logger=None, **kwargs):
        self.logger = logger
        super().__init__(*args, **kwargs)

    def handle(self):
        # Receive data from the client
        data = self.request.recv(1024).strip() # 1024 is the buffer size
        try:
            # Parse the received JSON data
            log_data = json_loads(data.decode('utf-8'))
            log_type = log_data.get("type", "info")
            message = log_data.get("message", "")
            origin = log_data.get("origin", "unknown")

            # Log the message using the Logger instance
            self.logger.log(log_type, message, origin)
        except JSONDecodeError:
            client_ip = self.client_address[0]
            self.logger.log(log_type="error", message="Invalid JSON data received from client", origin=client_ip)
        except Exception as ex:
            client_ip = self.client_address[0]
            self.logger.log(log_type="error", message=f"Error occured while handling log request: {str(ex)}", origin=client_ip)

if __name__ == "__main__":
    logger = Logger()
    HOST, PORT = "localhost", 9999

    # Create the server
    with TCPServer((HOST, PORT), lambda *args, **kwargs: LogRequestHandler(*args, logger=logger, **kwargs)) as server:
        print(f"Server started at {HOST}:{PORT}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("Shutting down server...")
        finally:
            logger.close()