import pymupdf
import json, sys, os
from datetime import date


def check(ctx):
    if "Fattura" not in ctx["subject"]:
        return False
    if "fattura" not in ctx["body_text"].lower():
        return False
    if "servizioclienti@telecomitalia.it" not in ctx["src"]:
        return False
    if not ctx["attachments"]:
        return False
    return True

def run(ctx):
    for file in ctx["attachments"]:
        if file.lower().endswith(".pdf"):
            doc = pymupdf.open(file)
            for page in doc:
                date = get_emission_date_from_text(page.get_text())
                if date:
                    date_str = date.strftime("%Y%m%d")
                    dst_root = os.getenv("DST_ROOT") or "."
                    dst_path = f"{dst_root}/Tim{date_str}.pdf"
                    dst_directory = os.path.dirname(dst_path)
                    if not os.path.exists(dst_directory):
                        os.makedirs(dst_directory, exist_ok=True)
                    with open(file, "rb") as src_f, open(dst_path, "wb") as dst_f:
                        dst_f.write(src_f.read())
                    return

def get_emission_date_from_text(text: str) -> date | None:
    for line in text.splitlines():
        if line.startswith("Data emissione: "):
            parts = line.split("Data emissione: ")[1].strip()
            return date.fromisoformat("-".join(parts.split("/")[::-1]))
    return None

ctx = json.load(sys.stdin)

if check(ctx):
    run(ctx)