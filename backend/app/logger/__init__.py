import logging
from logging.handlers import RotatingFileHandler
import os

class Logger:
    def __init__(self, prefix="", log_file_name="scraper.log", level=logging.INFO):
        self.logger = logging.getLogger(prefix)
        self.logger.setLevel(level)

        # Check if handlers already exist to avoid duplicate logs
        if not self.logger.handlers:
            # Create log directory if it doesn't exist
            log_dir = "logs"
            os.makedirs(log_dir, exist_ok=True)
            file_path = os.path.join(log_dir, log_file_name)

            # Add a file handler
            file_handler = RotatingFileHandler(file_path, maxBytes=1024*1024*5, backupCount=5)
            file_handler.setLevel(level)

            # Create a console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)

            # Create a formatter and set it for both handlers
            formatter = logging.Formatter(f'%(asctime)s - {prefix} - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)

            # Add the handlers to the logger
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    def get_logger(self):
        return self.logger
