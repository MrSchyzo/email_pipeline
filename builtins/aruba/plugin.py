from datetime import datetime
import json, sys, os, calendar

from email_pipeline.plugins.filesystem import copy_file

def check(ctx):
    if "La tua fattura per gli ordini di Aruba" not in ctx["subject"]:
        return False
    if "comunicazioni@staff.aruba.it" not in ctx["src"]:
        return False
    if not ctx["attachments"]:
        return False
    return True

def run(ctx):
    receipt = ctx["body_text"].split("la fattura nr. ")[1].split(" ")[0].strip()
    date = extract_date(ctx["body_text"])
    for file in ctx["attachments"]:
        if file.lower().endswith(".pdf"):
            dst_root = os.getenv("DST_ROOT") or "."
            dst_path = os.path.join(dst_root, f"{date}_fattura_{receipt}.pdf")
            copy_file(file, dst_path)

def extract_date(date_str: str) -> str:
    parts = date_str.split(" del ")[1].strip().split(" relativa ")[0].strip().replace("/", "-").split("-")
    parts.reverse()
    return "".join(parts)

ctx = json.load(sys.stdin)

if check(ctx):
    run(ctx)