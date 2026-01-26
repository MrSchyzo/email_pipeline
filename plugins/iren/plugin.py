import os
import time
from pathlib import Path

from bootstrap import state_file, file_saver, commodities, starting_headers, ctx
from invoices_not_found import InvoicesNotFoundException
from iren_helpers import extract_date, authorize, get_invoices_page, get_contracts, get_pdf_bytes
from logger import plugin_log
from email_pipeline.plugins.filesystem import ensure_directory

if "Emissione Bolletta" not in ctx["subject"]:
    exit(0)
if "la tua nuova bolletta" not in ctx["body_text"].lower():
    exit(0)
if "noreply@mail.clienti.irenyou.gruppoiren.it" not in ctx["src"]:
    exit(0)

folder = ensure_directory(os.getenv("DST_ROOT") or ".")
latest_invoice_date = Path(state_file).read_text().strip() if Path(state_file).exists() else "0"
recorded_invoice_date = "0"
remaining_attempts = 5

while remaining_attempts > 0:
    try:
        plugin_log.info("Authorizing user", extra={"user": os.getenv("USER")})
        _headers = authorize(os.getenv("USER"), os.getenv("PASSWORD"), starting_headers)

        plugin_log.info("Fetching contracts and invoices")
        contract_lookup = get_contracts(_headers)
        invoices = get_invoices_page(_headers)
        plugin_log.info("Fetched contracts and invoices",
                    extra={"contracts": len(contract_lookup), "invoices": len(invoices)})

        if not invoices:
            raise InvoicesNotFoundException("No invoices found")

        for invoice in invoices:
            emitted_at = extract_date(invoice["dataEmissione"])
            if emitted_at < latest_invoice_date:
                continue

            contract = contract_lookup[invoice["idFornituraDwh"]]

            time.sleep(0.5)
            file_saver.save_file(
                filename=f"{emitted_at}_{commodities[invoice["commodity"].upper()]}.pdf",
                content=get_pdf_bytes(invoice["nome"].strip(), contract["bpCode"], _headers),
                key=contract["number"]
            )
            plugin_log.info("Downloaded invoice PDF",
                        extra={"invoice_number": invoice["nome"], "contract_number": contract["number"],
                               "commodity": invoice["commodity"], "emitted_at": emitted_at})

            recorded_invoice_date = max(emitted_at, recorded_invoice_date)
            if recorded_invoice_date != "0":
                plugin_log.info("Updating latest invoice date", extra={"latest_invoice_date": recorded_invoice_date})
                Path(state_file).write_text(recorded_invoice_date)
        break
    except InvoicesNotFoundException as e:
        plugin_log.warning("Invoices not found, retrying...", extra={"remaining_attempt": remaining_attempts})
        remaining_attempts -= 1
        time.sleep(1)
    except BaseException as e:
        plugin_log.exception("Unhandled exception. Failing the process.", exc_info=True, stack_info=True)
        exit(1)
