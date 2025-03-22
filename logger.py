import logging

class Logger:
    def __init__(self):
        # Create a logger object
        self.logger = logging.getLogger("api_logger")
        self.logger.setLevel(logging.DEBUG)

        # Create a console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Create a file handler
        file_handler = logging.FileHandler("api.log")
        file_handler.setLevel(logging.DEBUG)

        # Create formatter objects and set the format of the log messages
        console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)

        # Add handlers to the logger
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def log(self, type, message):
        if type == "info":
            self.logger.info(message)
        elif type == "debug":
            self.logger.debug(message)
        elif type == "error":
            self.logger.error(message)
        elif type == "warning":
            self.logger.warning(message)
        else:
            self.logger.info(message)

    def close(self):
        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)