import logging

from bootstrap import ctx
from mail_pipeline.logger import logger

base = logger
plugin_log = logging.LoggerAdapter(base, {"plugin": "iren", "mail_uid": ctx["uid"]})
