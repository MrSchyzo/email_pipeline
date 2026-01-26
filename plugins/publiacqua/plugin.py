import json
import os
import re
import ssl
import sys
import urllib.request
import uuid

import certifi
from email_pipeline.logger import logger
from email_pipeline.plugins.filesystem import ensure_directory
from email_pipeline.plugins.lookup_file_saver import LookupFileSaver
from email_pipeline.plugins.selenium_utils import chrome_driver
from pymupdf import pymupdf
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


def find_link(text: str) -> str | None:
    for line in text.splitlines():
        if "href=\"https://bollettainterattiva.publiacqua" in line:
            link = line.split("href=\"")[1].strip().split("\"")[0].strip()
            return link
    return None


def click_on_close_icon(driver):
    try:
        close_icon = WebDriverWait(driver, 5).until(
            ec.element_to_be_clickable((By.CSS_SELECTOR, "svg.icon-close"))
        )
        close_icon.click()
    except BaseException as e:
        logger.exception(f"Failed to click on close icon: {e}", exc_info=True, stack_info=True)


def find_pdf_link(driver) -> str | None:
    try:
        pdf_link = WebDriverWait(driver, 5).until(
            ec.presence_of_element_located((By.CSS_SELECTOR, "a[href*='bolletta-web']"))
        )
        return pdf_link.get_attribute("href")
    except BaseException as e:
        logger.exception(f"Failed to find invoice PDF href: {e}", exc_info=True, stack_info=True)


def get_date(driver, date_iso: str) -> str:
    try:
        date_element = WebDriverWait(driver, 5).until(
            ec.presence_of_element_located((By.CSS_SELECTOR, "svg.c-riepilogo__timeline text:nth-of-type(4) tspan"))
        )
        return get_date_str(date_element.get_attribute("innerHTML"))
    except BaseException as e:
        logger.warning(f"Failed to find date on the page for mail {ctx['uid']}: {e}",
                       extra={"mail": ctx["uid"], "fallback_date": date_iso})
        return date_iso.replace("-", "").split("T")[0].strip()


def get_date_str(date_str: str) -> str:
    parts = date_str.strip().split("/")
    parts.reverse()
    parts[0] = f"20{parts[0]}"
    return "".join(parts)


def get_pdf_response(pdf_url: str):
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    return urllib.request.urlopen(pdf_url, context=ssl_context)


def get_contract_number(document: pymupdf.Document) -> str | None:
    for page in document:
        text = page.get_text()
        contract_number = text.split("CODICE CONTRATTO:")[-1].split("\n")[3].strip()
        if not re.search(r"\d{9,}", contract_number):
            continue
        return contract_number
    logger.warning("Failed to find contract number on the page", extra={"mail": ctx["uid"]})
    return None


ctx = json.load(sys.stdin)

if "MyPubliacqua: nuova bolletta web documento" not in ctx["subject"]:
    exit(0)
if "no-reply@publiacqua.it" not in ctx["src"]:
    exit(0)

file_saver = LookupFileSaver.from_json_config("config.json")

link = find_link(ctx["body_text"])
if not link:
    exit(0)

driver = chrome_driver()
try:
    driver.get(link)

    click_on_close_icon(driver)
    pdf_url = find_pdf_link(driver)

    if not pdf_url:
        logger.warning(f"Failed to find PDF URL on the page for mail {ctx['uid']}.")
        exit(0)

    date = get_date(driver, ctx.get("date", ""))

    with get_pdf_response(pdf_url) as response:
        dst_root = ensure_directory(os.getenv("DST_ROOT") or ".")
        tmp_path = dst_root / f"{uuid.uuid4().hex}.pdf"
        tmp_path.write_bytes(response.read())
        try:
            document = pymupdf.open(tmp_path)
            contract_number = get_contract_number(document)
            file_saver.save_file(filename=f"{date}_Acqua.pdf", content=response.read(), key=contract_number)
        finally:
            tmp_path.unlink(missing_ok=True)
finally:
    driver.quit()
