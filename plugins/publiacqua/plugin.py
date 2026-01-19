import json
import os
import ssl
import sys
import urllib.request

from mail_pipeline.plugins.selenium_utils import chrome_driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
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
            EC.element_to_be_clickable((By.CSS_SELECTOR, "svg.icon-close"))
        )
        close_icon.click()
    except:
        pass

def find_pdf_link(driver) -> str | None:
    try:
        pdf_link = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='bolletta-web']"))
        )
        return pdf_link.get_attribute("href")
    except:
        return None

def get_date(driver, date_iso: str) -> str:
    try:
        date_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "svg.c-riepilogo__timeline text:nth-of-type(4) tspan"))
        )
        return get_date_str(date_element.get_attribute("innerHTML"))
    except:
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
        

ctx = json.load(sys.stdin)

if "MyPubliacqua: nuova bolletta web documento" not in ctx["subject"]:
    exit(0)
if "no-reply@publiacqua.it" not in ctx["src"]:
    exit(0)

link = find_link(ctx["body_text"])
if not link:
    exit(0)

driver = chrome_driver()
try:
    driver.get(link)

    click_on_close_icon(driver)
    pdf_url = find_pdf_link(driver)

    if not pdf_url:
        print(f"Failed to find PDF URL on the page for mail {ctx['uid']}.")
        exit(0)

    date = get_date(driver, ctx.get("date", ""))

    with get_pdf_response(pdf_url) as response:
        dst_root = os.getenv("DST_ROOT") or "."
        dst_path = os.path.join(dst_root, f"{date}_Acqua.pdf")
        if not os.path.exists(os.path.dirname(dst_path)):
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
        with open(dst_path, "wb") as f:
            f.write(response.read())
finally:
    driver.quit()