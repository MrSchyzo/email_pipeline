import json
import logging
import os
import sys
import traceback
from datetime import datetime


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "message": record.getMessage(),
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "line_of_code": f"{record.pathname}:{record.lineno}",
            "level": record.levelname,
            "thread_name": record.threadName,
        }

        if hasattr(record, "extra_params"):
            for key, value in record.extra_params.items():
                log_record[key] = self._serialize(value)

        if record.exc_info:
            exc_type, exc_value, exc_tb = record.exc_info
            log_record["error_type"] = getattr(exc_type, "__name__", str(exc_type))
            log_record["error_msg"] = str(exc_value)
            log_record["stack_trace"] = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))

        if record.stack_info:
            log_record["stack_info"] = str(record.stack_info)

        standard_attrs = {
            'args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
            'funcName', 'levelname', 'levelno', 'lineno', 'module',
            'msecs', 'msg', 'name', 'pathname', 'process', 'processName',
            'relativeCreated', 'stack_info', 'thread', 'threadName', 'extra_params',
            'taskName'
        }
        for key, value in record.__dict__.items():
            if key not in standard_attrs:
                log_record[key] = self._serialize(value)

        return json.dumps(log_record)

    def _serialize(self, value):
        try:
            json.dumps(value)
            return value
        except (TypeError, OverflowError):
            return str(value)


class SafeStreamHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            super().emit(record)
        except BrokenPipeError:
            try:
                if self.stream:
                    self.stream.close()
            except BaseException:
                pass


def setup_logging():
    _logger = logging.getLogger("email_pipeline")
    _logger.setLevel(os.getenv("LOG_LEVEL", logging.INFO))

    _logger.extra_params = {}
    if os.getenv("LOG_PLUGIN"):
        _logger.extra_params["plugin_name"] = os.getenv("LOG_PLUGIN")
    if os.getenv("LOG_MAIL_UID"):
        _logger.extra_params["mail_uid"] = os.getenv("MAIL_UID")
    if os.getenv("LOG_PLUGIN_DIR"):
        _logger.extra_params["plugin_dir"] = os.getenv("PLUGIN_DIR")

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    _logger.addHandler(handler)
    _logger.propagate = False
    return _logger


logger = setup_logging()
