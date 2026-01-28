import json
import re
import sys
from datetime import datetime
from pathlib import Path

import pymupdf
from email_pipeline.plugins.lookup_file_saver import LookupFileSaver

plate_number_regex = re.compile(r"[A-Z]{2}\d{3}[A-Z]{2}")

def get_plate_number(document: pymupdf.Document) -> str | None:
    for page in document:
        text = page.get_text()
        if "\nAUTOVEICOLO" not in text:
            continue
        plate_num = text.split("\nAUTOVEICOLO")[0].split("\n")[-1].strip()
        if plate_number_regex.search(plate_num):
            return plate_num
    return None

ctx = json.load(sys.stdin)

if "SERVIZIO DI AVVISO SCADENZA BOLLO" not in ctx["subject"]:
    exit(0)
if not plate_number_regex.search(ctx["subject"]):
    exit(0)
if "tasseauto@regione.toscana.it" not in ctx["src"]:
    exit(0)
if not ctx["attachments"]:
    exit(0)

file_saver = LookupFileSaver.from_json_config("config.json")
date = ctx.get("date", None)
date = datetime.fromisoformat(date) if date else datetime.now()
for file in ctx["attachments"]:
    if not file.lower().endswith(".pdf"):
        continue
    doc = pymupdf.open(file)
    if plate_number := get_plate_number(doc):
        filename = f"{date.year}_Bollo.pdf"
        file_saver.save_file(
            filename=filename,
            content=Path(file).read_bytes(),
            key=plate_number
        )

exit(0)