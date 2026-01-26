import json
import random
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait

def chrome_driver(
        download_dir: str | None = None,
        headless: bool = True,
        force_open_pdf_external: bool = True,
        trace_calls: bool = False
) -> WebDriver:
    options = webdriver.ChromeOptions()

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    if headless:
        options.add_argument("--headless")
        options.add_argument("--window-size=3840,2160")
        options.add_argument("--force-device-scale-factor=1")

    prefs: dict[str, str | bool] = {
        "download.prompt_for_download": False,
        "directory_upgrade": True,
        "safebrowsing.enabled": True,
        "plugins.always_open_pdf_externally": force_open_pdf_external
    }
    if download_dir:
        prefs["download.default_directory"] = download_dir
    options.add_experimental_option("prefs", prefs)

    if trace_calls:
        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

    return webdriver.Chrome(options=options)

def start_tracking_network_calls(driver: WebDriver):
    driver.get_log("performance")
    driver.execute_cdp_cmd("Network.enable", {})

def point_and_type(driver: WebDriver, element: WebElement, text: str):
    point_and_click(driver, element)
    type_text(element, text)
    WebDriverWait(driver, 5).until(
        lambda d: element.get_attribute("value") == text
    )

def type_text(element: WebElement, text: str):
    for c in text:
        element.send_keys(c)
        time.sleep(random.uniform(0.05, 0.2))
    
def point_and_click(driver: WebDriver, element: WebElement):
    try:
        __point_and_click(driver, element)
    except:
        scroll_into_view(driver, element)
        __point_and_click(driver, element)

def __point_and_click(driver: WebDriver, element: WebElement):
    actions = ActionChains(driver)
    actions.move_to_element(element)

    for _ in range(3):
        x_offset = random.randint(-2, 2)
        y_offset = random.randint(-2, 2)
        actions.move_by_offset(x_offset, y_offset)
        actions.pause(0.1)

    actions.click().perform()

def scroll_into_view(driver: WebDriver, element: WebElement):
    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)

def dump_debug(
    driver: WebDriver,
    dump_directory: str = ".error_dump",
):
    root_path = Path(dump_directory)
    root_path.mkdir(parents=True, exist_ok=True)
    dump_network_logs(driver, dump_directory)

    html_path = root_path / "page.html"
    Path(html_path).write_text(driver.page_source)

    screenshot_path = root_path / "screenshot.png"
    width = driver.execute_script("return document.body.parentNode.scrollWidth")
    height = driver.execute_script("return document.body.parentNode.scrollHeight")
    driver.set_window_size(width, height)
    driver.save_screenshot(screenshot_path)


def dump_network_logs(driver: WebDriver, requests_dir_path: str = ".error_dump"):
    logs = driver.get_log("performance")
    traffic = {}

    for entry in logs:
        msg = json.loads(entry["message"])["message"]
        params = msg.get("params", {})
        rid = params.get("requestId")

        if msg["method"] == "Network.requestWillBeSent":
            traffic[rid] = {'request': params['request'], 'response': None}

        elif msg["method"] == "Network.responseReceived":
            if rid in traffic:
                traffic[rid]['response'] = params['response']
    for i, r in traffic.items():
        (Path(requests_dir_path)/f"request_{i}.json").write_text(json.dumps(r, indent=2))