import json
import logging
import sys
import uuid
from logging.handlers import RotatingFileHandler
from typing import Optional

from pythonjsonlogger.json import JsonFormatter


class CustomJsonFormatter(JsonFormatter):
    # Custom JSON formatter to add more field
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        # Enviornments
        log_record["app"] = "interviewpilot"
        log_record["level"] = record.levelname
        log_record["module"] = record.module


class EnterpriseLogger:
    _instance: Optional["EnterpriseLogger"] = None
    _logger: Optional[logging.Logger] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._logger is None:
            self._setup_logger()

    def _setup_logger(self):
        self._logger = logging.getLogger("interviewpilot")
        self._logger.setLevel(logging.DEBUG)

        # Prevent duplicate handlers
        if self._logger.handlers:
            return

        # Console Handler: INFO
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(console_formatter)

        # File Handler: DEBUG
        file_handler = RotatingFileHandler(
            "logs/interviewpilot.log", maxBytes=10_485_769, backupCount=10  # 10MB
        )
        file_handler.setLevel(logging.DEBUG)
        json_formatter = CustomJsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s %(module)s %(funcName)s %(lineno)d"
        )
        file_handler.setFormatter(json_formatter)
        self._logger.addHandler(file_handler)

    def get_logger(self, module_name: str) -> logging.Logger:
        # Returns a logger with a child prefix for this module
        return logging.getLogger(f"interviewpilot.{module_name}")


# Singleton instance
logger = EnterpriseLogger()


def get_logger(module_name: str) -> logging.Logger:
    # Convenience function to get a module-scoped logger.
    return logger.get_logger(module_name)
