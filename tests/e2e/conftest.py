"""Global test fixtures for end-to-end tests."""

from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

pytest.base_url = "https://127.0.0.1:5000"

ARTIFACTS_DIR = Path("artifacts")
ARTIFACTS_DIR.mkdir(exist_ok=True)


@pytest.fixture
def driver(request):
    """Selenium WebDriver fixture."""
    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    options.set_capability("acceptInsecureCerts", True)
    _driver = webdriver.Firefox(options=options)
    _driver.set_window_size(1920, 1080)
    _driver.get(pytest.base_url)

    body = _driver.find_element(By.TAG_NAME, "body")
    wait = WebDriverWait(_driver, timeout=10)
    wait.until(lambda _: body.is_displayed())

    yield _driver

    test_name = request.node.originalname
    screenshot_path = ARTIFACTS_DIR / f"{test_name}.png"
    _driver.get_full_page_screenshot_as_file(str(screenshot_path))

    _driver.quit()
