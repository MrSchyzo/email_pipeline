import base64
import json
import os
import sys
import time
import uuid
from pathlib import Path
import functools

import certifi
import urllib3
from mail_pipeline.plugins.filesystem import ensure_directory

folder = ensure_directory(os.getenv("DST_ROOT") or ".")
state_file = ".latest_bill"
latest_bill_date = Path(state_file).read_text().strip() if Path(state_file).exists() else "0"
recorded_bill_date = "0"

http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
root = "https://clickiren-gateway.clienti.irenlucegas.it"
headers = {
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Content-Type": "application/json",
    "Connection": "keep-alive",
    "Accept-Language": "it-IT",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://clienti.irenyou.gruppoiren.it",
    "Referer": "https://clienti.irenyou.gruppoiren.it/area-riservata/spese",
    "Host": "clickiren-gateway.clienti.irenlucegas.it",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
}

def compare_bills_emission(a: dict[str, str], b: dict[str, str]) -> int:
    date_a = a["dataEmissione"]
    date_b = b["dataEmissione"]
    return (date_a > date_b) - (date_a < date_b)

def extract_date(date_str: str) -> str:
    pieces = date_str.split(".")
    pieces.reverse()
    return "".join(pieces)

def get_token(username: str, password: str, headers: dict[str, str]) -> str:
    payload = json.dumps({"email": username, "password": password}).encode("utf-8")
    res = http.request("POST", f"{root}/v2/api/authenticate", body=payload, headers=headers)
    return json.loads(res.data.decode("utf-8"))["data"]["id_token"]

def get_bills_page(heads: dict[str, str]) -> list[dict[str, str]]:
    payload = json.dumps({"page": 1}).encode("utf-8")
    bills = []
    attempts = 5
    while not bills and attempts > 0:
        time.sleep(1)
        attempts -= 1
        res = http.request("POST", f"{root}/v3/api/archivio-bollette-p", headers=heads, body=payload)
        bills = json.loads(res.data.decode("utf-8"))["data"]["fatture"]
        bills.sort(key=functools.cmp_to_key(compare_bills_emission), reverse=False)
        print(f"Found {len(bills)} bills")
    return bills

def get_contracts(heads: dict[str, str]) -> dict[str, str]:
    res = http.request("GET", f"{root}/v3/api/ricerca/fornitura", headers=heads)
    contracts = json.loads(res.data.decode("utf-8"))["data"]["contracts"]
    return { contract["idFornitura"]: contract["bpAccountSAP"] for contract in contracts }

commodities = {
    "GAS": "Gas",
    "ELE": "Luce",
    "WASTE": "Rifiuti",
    "H20": "Acqua",
}

ctx = json.load(sys.stdin)

if "Emissione Bolletta" not in ctx["subject"]:
    exit(0)
if "la tua nuova bolletta" not in ctx["body_text"].lower():
    exit(0)
if "noreply@mail.clienti.irenyou.gruppoiren.it" not in ctx["src"]:
    exit(0)

total_attempts = 10
while total_attempts > 0:
    token = get_token(os.getenv("USER"), os.getenv("PASSWORD"), headers)

    headers["Authorization"] = f"Bearer {token}"
    headers["uuid"] = str(uuid.uuid4())

    contract_lookup = get_contracts(headers)
    receipts = get_bills_page(headers)
    for receipt in receipts:
        id_fornitura = receipt["idFornituraDwh"].strip()
        emitted_at = extract_date(receipt["dataEmissione"])
        if emitted_at < latest_bill_date:
            continue
        postfix = commodities[receipt["commodity"].upper()]
        number = receipt["nome"].strip()
        time.sleep(0.5)
        partner_code = contract_lookup[id_fornitura]
        response = http.request("GET", f"{root}/v3/api/downloadpdfbpm?numeroFattura={number}&businessPartner={partner_code}", headers=headers)
        pdf_contents_b64 = json.loads(response.data.decode("utf-8"))["data"]["document"]
        target_name = f"{emitted_at}_{postfix}.pdf"
        if pdf_contents_b64:
            (Path(f"{folder}")/target_name).write_bytes(base64.b64decode(pdf_contents_b64))
            recorded_bill_date = max(emitted_at, recorded_bill_date)
            Path(state_file).write_text(recorded_bill_date)
            if recorded_bill_date != "0":
                Path(state_file).write_text(recorded_bill_date)
        else:
            print(f"No PDF found for bill")
    if not receipts:
        total_attempts -= 1
    else:
        break

