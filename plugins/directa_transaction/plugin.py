import pymupdf
import json, sys, os
from datetime import datetime

def check(ctx):
    if "Nota informativa" not in ctx["subject"]:
        return False
    if "ordine eseguito" not in ctx["body_text"].lower():
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
                    dst_directory = os.path.dirname(dst_path)
                    if not os.path.exists(dst_directory):
                        os.makedirs(dst_directory, exist_ok=True)
                    with open(file, "rb") as src_f, open(dst_path, "wb") as dst_f:
                        dst_f.write(src_f.read())
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