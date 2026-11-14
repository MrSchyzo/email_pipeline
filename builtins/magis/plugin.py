import json
import os
import re
import sys
from pathlib import Path

import pymupdf
from email_pipeline.logger import logger
from email_pipeline.plugins.lookup_file_saver import LookupFileSaver

SUBJECT_RE = re.compile(r"Fattura nr\..*\bdel\s+(\d{2})/(\d{2})/(\d{4})")
OFFER_RE = re.compile(r"Codice offerta:\s*(\S+)")


def get_offer_code(pdf_path: str) -> str | None:
    with pymupdf.open(pdf_path) as doc:
        for page in doc:
            match = OFFER_RE.search(page.get_text())
            if match:
                return match.group(1)
    return None


ctx = json.load(sys.stdin)

if "paperless@gruppomagis.it" not in ctx["src"]:
    exit(0)
subject_match = SUBJECT_RE.search(ctx["subject"])
if not subject_match:
    exit(0)
pdfs = [f for f in ctx["attachments"] if f.lower().endswith(".pdf")]
if not pdfs:
    exit(0)

day, month, year = subject_match.groups()
file_saver = LookupFileSaver.from_json_config("config.json", os.getenv("DST_ROOT") or ".")

for pdf in pdfs:
    offer_code = get_offer_code(pdf)
    filename = f"{year}{month}{day}_{Path(pdf).name}"
    file_saver.save_file(filename=filename, content=Path(pdf).read_bytes(), key=offer_code)
    logger.info("Saved Magis invoice", extra={"file": filename, "offer_code": offer_code})
