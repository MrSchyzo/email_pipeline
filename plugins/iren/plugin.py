import json
import os
import random
import sys
import time
from pathlib import Path
import traceback

from mail_pipeline.plugins.filesystem import ensure_directory, wait_for_new_file
from mail_pipeline.plugins.selenium_utils import dump_debug, point_and_click, point_and_type, chrome_driver, start_tracking_network_calls
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

ctx = json.load(sys.stdin)

if "Emissione Bolletta" not in ctx["subject"]:
    exit(0)
if "la tua nuova bolletta" not in ctx["body_text"].lower():
    exit(0)
if "noreply@mail.clienti.irenyou.gruppoiren.it" not in ctx["src"]:
    exit(0)

with_gui = os.getenv("GUI") == "true"
folder = ensure_directory(os.getenv("DST_ROOT") or ".")
driver = chrome_driver(folder, headless=not with_gui, trace_calls=True)
state_file = ".latest_bill"
latest_bill_date = Path(state_file).read_text().strip() if Path(state_file).exists() else "0"
try:
    recorded_bill_date = "0"
    wait = WebDriverWait(driver, 5)
    driver.get("https://clienti.irenyou.gruppoiren.it/login")

    try:
        WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.iubenda-cs-close-btn"))).click()
    except:
        pass

    user_field = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input#email-o-username")))
    password_field = driver.find_element(By.CSS_SELECTOR, "input#password")
    start_tracking_network_calls(driver)
    point_and_type(driver, user_field, os.getenv("USER"))
    point_and_type(driver, password_field, os.getenv("PASSWORD"))
    time.sleep(random.uniform(0.5, 1.5))
    point_and_click(
        driver,
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'ACCEDI')]")))
    )

    wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//span[contains(@class, 'mdc-tab__content')]//span[contains(text(), 'Bollette')]")
    )).click()

    cards = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "iren-ar-spese-card")))
    for i in range(len(cards)):
        current_cards = driver.find_elements(By.TAG_NAME, "iren-ar-spese-card")
        card = current_cards[i]

        try:
            card.click()

            img = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "img.commodity-icon-summary")))
            commodity = img.get_attribute("alt").strip()

            emessa_div = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Emessa il')]")))
            emessa_text = emessa_div.get_attribute("innerText").strip()
            emessa_date_str = emessa_text.split("Emessa il")[-1].strip().split(".")
            emessa_date_str.reverse()
            emessa_date = "".join(emessa_date_str)

            if emessa_date <= latest_bill_date:
                break

            if "Gas" in commodity:
                postfix = "Gas"
            elif "Luce" in commodity:
                postfix = "Luce"
            elif "Ambiente" in commodity:
                postfix = "Rifiuti"
            elif "Acqua" in commodity:
                postfix = "Acqua"
            else:
                postfix = "Bolletta"

            expected_filename = f"{postfix}_{emessa_date}.pdf"

            wait.until(
                EC.element_to_be_clickable((By.XPATH, "//mat-select[//span[contains(text(), 'Azioni')]]"))
            ).click()

            files_before_download = set(os.listdir(folder))
            wait.until(
                EC.element_to_be_clickable((By.XPATH, "//mat-option//span[contains(text(), 'Scarica Bolletta')]"))
            ).click()
            downloaded_file = wait_for_new_file(folder, files_before_download, timeout=10)
            # Rename the downloaded file to expected filename
            if downloaded_file:
                downloaded_path = Path(folder) / downloaded_file
                dst_path = Path(folder) / expected_filename
                downloaded_path.rename(dst_path)
                print(f"Downloaded bill saved to {dst_path.resolve()}")

            recorded_bill_date = emessa_date if emessa_date > recorded_bill_date else recorded_bill_date

            driver.find_element(By.TAG_NAME, "body").send_keys("\ue00c")  # Escape key

            wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Torna a Bollette')]"))
            ).click()

            wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "iren-ar-spese-card")))
        except Exception as e:
            print(f"Skipping card {i} as it doesn't match criteria or error occurred: {e}")
            continue

    if recorded_bill_date != "0":
        Path(state_file).write_text(recorded_bill_date)     
except Exception as e:
    traceback.print_exc()
    dump_debug(driver)
finally:
    driver.quit()