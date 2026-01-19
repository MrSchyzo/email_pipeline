import json
import os
from pathlib import Path
import sys
import base64
import traceback
from mail_pipeline.plugins.filesystem import ensure_directory, wait_for_new_file
from mail_pipeline.plugins.selenium_utils import chrome_driver, dump_debug, point_and_click, point_and_type
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

ctx = json.load(sys.stdin)

if "Notifica Pubblicazione Cedolini" not in ctx["subject"]:
    exit(0)
if "portale@leoniweb.it" not in ctx["src"]:
    exit(0)
if "Cedolini del periodo&nbsp;" not in ctx["body_text"]:
    exit(0)

expected_period = ctx["body_text"].split("Cedolini del periodo&nbsp;")[1].split("<")[0].strip()
folder = ensure_directory(os.getenv("DST_ROOT") or ".")
driver = chrome_driver(folder, headless=True, force_open_pdf_external=True)
wait = WebDriverWait(driver, 10)

try:
    driver.get("https://portale.bgt-grantthornton.it/HRLeoniWeb/jsp/login.jsp")

    user_field = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@name='m_cUserName']")))
    password_field = driver.find_element(By.XPATH, "//input[@name='m_cPassword']")
    point_and_type(driver, user_field, os.getenv("USER"))
    point_and_type(driver, password_field, os.getenv("PASSWORD"))
    login_btn = driver.find_element(By.XPATH, "//input[@type='submit' and @value='Login']")
    point_and_click(driver, login_btn)

    wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, "//iframe[@id]")))
    myspace_tab = wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(@class, 'tab_text') and contains(text(), 'MySpace')]")))
    point_and_click(driver, myspace_tab)

    # find table in column_shell
    column_shell = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "column_shell")))
    first_tr = wait.until(EC.presence_of_element_located((By.XPATH, f"//span[@title='Apri documento' and contains(text(), '{expected_period}')]")))
    point_and_click(driver, first_tr)

    # handle new window
    wait.until(EC.number_of_windows_to_be(2))
    original_window = driver.current_window_handle
    for window_handle in driver.window_handles:
        if window_handle != original_window:
            driver.switch_to.window(window_handle)
            break

    # download PDF
    files_before_download = set(os.listdir(folder))
    filename_str = expected_period.split("-")
    filename_str.reverse()
    file_path = Path(folder) / ("".join(filename_str) + "_BustaH.pdf")

    new_file = wait_for_new_file(folder, files_before_download, timeout=5)
    if new_file.endswith(".pdf"):
        os.rename(new_file, file_path)
    else:
        print("Downloaded file is not a PDF.")
except Exception as e:
    traceback.print_exc()
    dump_debug(driver, html_path=".iren_dump.html", screenshot_path=".iren_dump.png")
finally:
    driver.quit()

