import json
import os
import sys
import traceback
from pathlib import Path

from email_pipeline.logger import logger
from email_pipeline.plugins.filesystem import ensure_directory, wait_for_new_file
from email_pipeline.plugins.selenium_utils import chrome_driver, dump_debug, point_and_click, point_and_type
from selenium.common import UnexpectedAlertPresentException, TimeoutException
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
driver = chrome_driver(str(folder), headless=True, force_open_pdf_external=True, trace_calls=True)
wait = WebDriverWait(driver, 10)


def enter_credentials(user=os.getenv("USER"), password=os.getenv("PASSWORD")):
    user_field = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@name='m_cUserName']")))
    password_field = driver.find_element(By.XPATH, "//input[@name='m_cPassword']")
    point_and_type(driver, user_field, user)
    point_and_type(driver, password_field, password)
    login_btn = driver.find_element(By.XPATH, "//input[@type='submit' and @value='Login']")
    point_and_click(driver, login_btn)


def go_to_myspace_tab():
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, "//iframe[@id]")))
    myspace_tab = wait.until(EC.presence_of_element_located(
        (By.XPATH, "//span[contains(@class, 'tab_text') and contains(text(), 'MySpace')]")))
    point_and_click(driver, myspace_tab)


def open_download_link():
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "column_shell")))
    first_tr = wait.until(
        EC.presence_of_element_located((By.XPATH, f"//*[(contains(text(), 'Libro unico di {expected_period}'))]")))
    point_and_click(driver, first_tr)


def yeah_yeah_whatever(timeout=5):
    try:
        WebDriverWait(driver, timeout).until(EC.alert_is_present()).accept()
    except TimeoutException:
        pass


def switch_to_pdf_window():
    try:
        yeah_yeah_whatever(2)
        wait.until(EC.number_of_windows_to_be(2))
    except UnexpectedAlertPresentException:
        logger.warning("Alert detected while waiting for the new window, accepting it")
        wait.until(EC.number_of_windows_to_be(2))

    original_window = driver.current_window_handle
    for window_handle in driver.window_handles:
        if window_handle != original_window:
            driver.switch_to.window(window_handle)
            break


def wait_for_file_and_rename(files_before_download: set) -> Path:
    new_file = wait_for_new_file(str(folder), files_before_download, timeout=10)
    filename_str = expected_period.split("-")
    filename_str.reverse()
    file_path = folder / ("".join(filename_str) + "_BustaH.pdf")
    os.rename(new_file, file_path)
    return file_path


try:
    files_before_download = set(os.listdir(folder))
    user = os.getenv("USER")
    driver.get("https://portale.bgt-grantthornton.it/HRLeoniWeb/jsp/login.jsp")
    logger.debug("Landed into BGT portal", extra={"user": user})

    enter_credentials(user, os.getenv("PASSWORD"))
    logger.debug("Entered credentials", extra={"user": user})

    go_to_myspace_tab()
    logger.debug("Switched to MySpace tab, now looking for the document of the right period", extra={"period": expected_period})

    open_download_link()
    logger.debug("Clicked on the document link, now waiting for downloading", extra={"period": expected_period})

    switch_to_pdf_window()
    logger.debug("Window has been swapped to download the PDF. Now waiting for download completion", extra={"period": expected_period})

    file_path = wait_for_file_and_rename(files_before_download)
    logger.info("PDF downloaded", extra={"period": expected_period, "path": file_path})
except BaseException as e:
    traceback.print_exc()
    dump_debug(driver)
    exit(1)
finally:
    driver.quit()

