import pymupdf
import json, sys, os

from email_pipeline.plugins.filesystem import copy_file
from datetime import datetime

def check(ctx):
    if "Nota informativa" not in ctx["subject"]:
        return False
    if "ordine eseguito" not in ctx["body_text"].lower():
        return False
    if "automatica@directa.it" not in ctx["src"]:
        return False
    if not ctx["attachments"]:
        return False
    return True

def run(ctx):
    date = ctx.get("date", None)
    date = datetime.fromisoformat(date) if date else datetime.now()
    date_str = date.strftime("%Y%m%d")
    
    for file in ctx["attachments"]:
        if file.lower().endswith(".pdf"):
            doc = pymupdf.open(file)
            for page in doc:
                isin = get_isin_from_text(page.get_text())
                if isin:
                    dst_root = os.getenv("DST_ROOT") or "."
                    dst_path = f"{dst_root}/{date_str}_{isin}.pdf"
                    copy_file(file, dst_path)
                    return

def get_isin_from_text(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("per l'acquisto di:") and "ISIN" in line:
            parts = line.split(" ")
            try:
                isin_index = parts.index("ISIN") + 1
                isin = parts[isin_index].strip()
                return isin
            except (ValueError, IndexError):
                continue
    return None

ctx = json.load(sys.stdin)

if check(ctx):
    run(ctx)