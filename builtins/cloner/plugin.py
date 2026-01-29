import json
import os
import re
import shutil
import sys
from pathlib import Path

from email_pipeline.logger import logger


class Cloner:
    def __init__(self, ctx, config):
        self.ctx = ctx
        self.config = config

    def match_condition(self, condition, data):
        if "all" in condition:
            return all(self.match_condition(sub, data) for sub in [condition["all"]] if isinstance(sub, dict))
        if "any" in condition:
            return any(self.match_condition(sub, data) for sub in [condition["any"]] if isinstance(sub, dict))

        match_results = []
        if "from" in condition:
            match_results.append(bool(re.search(condition["from"], data.get("src", ""))))
        if "body" in condition:
            match_results.append(bool(re.search(condition["body"], data.get("body_text", ""))))
        if "subject" in condition:
            match_results.append(bool(re.search(condition["subject"], data.get("subject", ""))))

        return all(match_results) if match_results else True

    def run(self):
        if not isinstance(self.config, list):
            return

        for i, entry in enumerate(self.config):
            logger.debug(f"Checking rule [{i}]")
            conditions_to_check = []
            if "all" in entry:
                conditions_to_check.append(entry["all"])
            if "any" in entry:
                conditions_to_check.append({"any": entry["any"]})

            if base_cond := {k: entry[k] for k in ["from", "body", "subject"] if k in entry}:
                conditions_to_check.append(base_cond)

            if all(self.match_condition(c, self.ctx) for c in conditions_to_check):
                logger.info("Copying attachments", extra={"dst": Path(entry.get("to")).resolve(), "rule": str(i)})
                self.copy_attachments(entry.get("to"))

    def copy_attachments(self, destination):
        if not destination:
            return

        uid = self.ctx['uid']
        dest_path = Path(destination)
        dest_path.mkdir(parents=True, exist_ok=True)

        for attachment in self.ctx.get("attachments", []):
            src_file = Path(attachment)
            cleaned_filename = src_file.name.replace(f"{uid}_", "") if uid in src_file.name else src_file.name
            if src_file.exists():
                shutil.copy2(src_file, dest_path / cleaned_filename)

ctx = json.load(sys.stdin)

try:
    with open("config.json", "r") as f:
        config = json.load(f)
except FileNotFoundError:
    config = []

os.makedirs(os.getenv("DST_ROOT", "."), exist_ok=True)
os.chdir(os.getenv("DST_ROOT", "."))

cloner = Cloner(ctx, config)
cloner.run()

exit(0)