import json, sys

def check(ctx):
    if "Nota informativa" not in ctx["subject"]:
        return False
    if "ordine eseguito" not in ctx["body_text"].lower():
        return False
    if not ctx["attachments"]:
        return False
    return True

def run(ctx):
    for file in ctx["attachments"]:
        print(f"Processing attachment: {file}")

ctx = json.load(sys.stdin)

if check(ctx):
    run(ctx)