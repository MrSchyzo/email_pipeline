import json
import sys

import certifi
import urllib3
from mail_pipeline.plugins.lookup_file_saver import LookupFileSaver

ctx = json.load(sys.stdin)

file_saver = LookupFileSaver.from_json_config("config.json")

commodities = {
    "GAS": "Gas",
    "ELE": "Luce",
    "WASTE": "Rifiuti",
    "H20": "Acqua",
}

http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
root = "https://clickiren-gateway.clienti.irenlucegas.it"
starting_headers = {
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

state_file = ".latest_invoice"
