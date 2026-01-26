import logging

from bootstrap import ctx
from email_pipeline.logger import logger

base = logger
plugin_log = logging.LoggerAdapter(base, {"plugin": "iren", "mail_uid": ctx["uid"]})
