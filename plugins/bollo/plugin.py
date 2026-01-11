from datetime import datetime
import json, sys, os

def check(ctx):
    if "SERVIZIO DI AVVISO SCADENZA BOLLO" not in ctx["subject"]:
        return False
    if not ctx["attachments"]:
        return False
    return True

def run(ctx):
    date = ctx.get("date", None)
    date = datetime.fromisoformat(date) if date else datetime.now()
    for file in ctx["attachments"]:
        if file.lower().endswith(".pdf"):
            dst_root = os.getenv("DST_ROOT") or "."
            dst_path = os.path.join(dst_root, f"{date.year}_Bollo.pdf")
            dst_directory = os.path.dirname(dst_path)
            if not os.path.exists(dst_directory):
                os.makedirs(dst_directory, exist_ok=True)
            with open(file, "rb") as src_f, open(dst_path, "wb") as dst_f:
                dst_f.write(src_f.read())

ctx = json.load(sys.stdin)

if check(ctx):
    run(ctx)