import html
import json
import os
import re
import sys
from datetime import date, datetime, timedelta

import boto3
import requests
from botocore import UNSIGNED
from botocore.config import Config
from botocore.exceptions import ClientError
from email_pipeline.logger import logger
from email_pipeline.plugins.lookup_file_saver import LookupFileSaver
from pycognito.aws_srp import AWSSRP

SUBJECT_RE = re.compile(r"fattura .* disponibile", re.I)
PDF_KINDS = {"detailed": "dettaglio", "summarized": "sintetica"}
UTILITIES = {"GA": "Gas", "EE": "Luce"}
# observed: the email arrives the day the bill is emitted; slack both ways covers delays and clock/timezone skew
WINDOW = timedelta(days=5)


def site_config() -> dict[str, str]:
    """Cognito ids and API base are embedded in every nen.it page, so a redeploy can't silently break us."""
    page = html.unescape(requests.get("https://nen.it/caricamento", timeout=30).text)
    config = {}
    for key in ("appUserPool", "appUserPoolClient", "region", "awsBaseurl"):
        match = re.search(rf'"{key}":"([^"]+)"', page)
        if not match:
            raise RuntimeError(f"'{key}' not found in nen.it page: the site layout changed")
        config[key] = match.group(1)
    return config


def login(user: str, password: str, config: dict[str, str]) -> str:
    """Same flow as the site (Amplify): CUSTOM_AUTH starting with an SRP password check. Returns the IdToken."""
    client_id = config["appUserPoolClient"]
    idp = boto3.client("cognito-idp", region_name=config["region"], config=Config(signature_version=UNSIGNED))
    srp = AWSSRP(username=user, password=password, pool_id=config["appUserPool"], client_id=client_id, client=idp)
    params = srp.get_auth_params()
    challenge = idp.initiate_auth(ClientId=client_id, AuthFlow="CUSTOM_AUTH",
                                  AuthParameters={**params, "CHALLENGE_NAME": "SRP_A"})
    result = idp.respond_to_auth_challenge(
        ClientId=client_id, ChallengeName="PASSWORD_VERIFIER", Session=challenge["Session"],
        ChallengeResponses=srp.process_challenge(challenge["ChallengeParameters"], params))
    return result["AuthenticationResult"]["IdToken"]


ctx = json.load(sys.stdin)

if "nen.it" not in ctx["src"] or not SUBJECT_RE.search(ctx["subject"]):
    exit(0)

file_saver = LookupFileSaver.from_json_config("config.json", os.getenv("DST_ROOT") or ".")
email_date = datetime.fromisoformat(ctx["date"]).date() if ctx.get("date") else date.today()
since, until = email_date - WINDOW, email_date + WINDOW
periods = {since.year, until.year}  # bills are listed per calendar year
api = requests.Session()


def get_json(method: str, url: str, **kwargs):
    response = api.request(method, url, timeout=30, **kwargs)
    response.raise_for_status()
    return response.json()


phase = "reading Cognito config from nen.it"
downloaded = 0
try:
    config = site_config()
    api_root = config["awsBaseurl"]

    phase = "logging in"
    try:
        api.headers["Authorization"] = login(os.getenv("USER"), os.getenv("PASSWORD"), config)  # raw IdToken, no "Bearer"
    except ClientError as e:
        # don't fail the pipeline: a broken login must not block other plugins or later emails
        logger.error("NeN login failed, skipping", extra={"user": os.getenv("USER"), "error_msg": str(e)})
        exit(0)

    phase = "listing home contexts from /profile"
    # closed supplies still get a final bill, so check every home context, not only active ones
    home_context_ids = {s["homeContextId"] for s in get_json("GET", f"{api_root}/profile")["subscriptions"]}
    for home_context_id in home_context_ids:
        for period in periods:
            phase = f"listing bills of home context {home_context_id} for {period}"
            for invoice in get_json("GET", f"{api_root}/bills/details/{home_context_id}", params={"period": period})["invoices"]:
                emitted_at = invoice["emissionDate"]  # YYYY-MM-DD
                if not since.isoformat() <= emitted_at <= until.isoformat():
                    continue
                utility = UTILITIES.get(invoice["utility"], invoice["utility"])
                for kind, suffix in PDF_KINDS.items():
                    phase = f"downloading {kind} PDF of bill {invoice['number']}"
                    url = get_json("POST", f"{api_root}/documents/private/download",
                                   json={"path": invoice["billPath"][kind]})["url"]
                    pdf = requests.get(url, timeout=60)  # presigned S3 url: no auth header
                    pdf.raise_for_status()
                    file_saver.save_file(filename=f"{emitted_at.replace('-', '')}_{utility}_{suffix}.pdf",
                                         content=pdf.content, key=invoice["subscriptionId"])
                logger.info("Downloaded NeN invoice",
                            extra={"invoice_number": invoice["number"], "subscription_id": invoice["subscriptionId"],
                                   "utility": invoice["utility"], "emitted_at": emitted_at})
                downloaded += 1
except Exception as e:
    logger.exception("NeN plugin failed", extra={"phase": phase, "error_msg": str(e)})
    exit(1)

if not downloaded:
    logger.warning("NeN bill email but no bill emitted near its date",
                   extra={"since": since.isoformat(), "until": until.isoformat(), "home_contexts": len(home_context_ids)})
