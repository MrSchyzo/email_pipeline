import base64
import copy
import functools
import json
import time
import uuid

from bootstrap import root, http
from logger import plugin_log


def compare_invoices_emission(a: dict[str, str], b: dict[str, str]) -> int:
    date_a = a["dataEmissione"]
    date_b = b["dataEmissione"]
    return (date_a > date_b) - (date_a < date_b)


def extract_date(date_str: str) -> str:
    pieces = date_str.split(".")
    pieces.reverse()
    return "".join(pieces)


def authorize(username: str, password: str, headers: dict[str, str]) -> dict[str, str]:
    _headers = copy.deepcopy(headers)
    _payload = json.dumps({"email": username, "password": password}).encode("utf-8")
    _response = http.request("POST", f"{root}/v2/api/authenticate", body=_payload, headers=_headers)
    _headers["Authorization"] = f"Bearer {json.loads(_response.data.decode("utf-8"))["data"]["id_token"]}"
    _headers["uuid"] = str(uuid.uuid4())
    return _headers


def get_invoices_page(heads: dict[str, str]) -> list[dict[str, str]]:
    payload = json.dumps({"page": 1}).encode("utf-8")
    remaining_attempts = 5
    while remaining_attempts > 0:
        remaining_attempts -= 1
        res = http.request("POST", f"{root}/v3/api/archivio-bollette-p", headers=heads, body=payload)
        invoices = json.loads(res.data.decode("utf-8"))["data"]["fatture"]
        invoices.sort(key=functools.cmp_to_key(compare_invoices_emission), reverse=False)
        if invoices:
            return invoices
        plugin_log.info("No invoices found, retrying...", extra={"remaining_attempt": remaining_attempts})
        time.sleep(1)
    return []


def get_contracts(heads: dict[str, str]) -> dict[str, dict[str, str]]:
    res = http.request("GET", f"{root}/v3/api/ricerca/fornitura", headers=heads)
    contracts = json.loads(res.data.decode("utf-8"))["data"]["contracts"]
    return {c["idFornitura"]: {"bpCode": c["bpAccountSAP"], "number": c["irenContractNumber"]} for
            c in contracts}


def get_pdf_bytes(number: str, partner_code: str, headers: dict[str, str]) -> bytes:
    response = http.request("GET",
                            f"{root}/v3/api/downloadpdfbpm?numeroFattura={number}&businessPartner={partner_code}",
                            headers=headers)
    return base64.b64decode(json.loads(response.data.decode("utf-8"))["data"]["document"])
