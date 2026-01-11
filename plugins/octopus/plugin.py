from datetime import datetime
import json, sys, os, calendar

def check(ctx):
    if "La tua bolletta Octopus Energy - " not in ctx["subject"]:
        return False
    if "ciao@octopusenergy.it" not in ctx["src"]:
        return False
    if not ctx["attachments"]:
        return False
    return True

def run(ctx):
    type = ctx["subject"].split("-")[-1].strip()
    date = ctx.get("date", None)
    date = datetime.fromisoformat(date) if date else datetime.now()
    date = subtract_one_month(date)
    for file in ctx["attachments"]:
        if file.lower().endswith(".pdf"):
            dst_root = os.getenv("DST_ROOT") or "."
            dst_path = os.path.join(dst_root, f"{date.strftime("%Y%m")}_{type}.pdf")
            dst_directory = os.path.dirname(dst_path)
            if not os.path.exists(dst_directory):
                os.makedirs(dst_directory, exist_ok=True)
            with open(file, "rb") as src_f, open(dst_path, "wb") as dst_f:
                dst_f.write(src_f.read())

def subtract_one_month(dt: datetime) -> datetime:
    year = dt.year
    month = dt.month - 1
    if month == 0:
        month = 12
        year -= 1
    day = min(dt.day, calendar.monthrange(year, month)[1])
    return dt.replace(year=year, month=month, day=day)

ctx = json.load(sys.stdin)

if check(ctx):
    run(ctx)