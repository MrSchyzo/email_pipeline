from datetime import datetime
import json, sys

def check(ctx):
    if "SERVIZIO DI AVVISO SCADENZA BOLLO" not in ctx["subject"]:
        return False
    if not ctx["attachments"]:
        return False
    return True

def run(ctx):
    date = ctx.get("date", None)
    date = datetime.fromisoformat(date) if date else None
    for file in ctx["attachments"]:
        print(f"UN BOLLOOOOOOOOOOOO! {file}: {date}")

ctx = json.load(sys.stdin)

if check(ctx):
    run(ctx)