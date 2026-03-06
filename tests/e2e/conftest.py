"""Global test fixtures for end-to-end tests."""

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

pytest.base_url = "https://127.0.0.1:5000"


@pytest.fixture
def driver():
    """Selenium WebDriver fixture."""
    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    _driver = webdriver.Firefox(options=options)
    _driver.get(pytest.base_url)

    body = _driver.find_element(By.TAG_NAME, "body")
    wait = WebDriverWait(_driver, timeout=10)
    wait.until(lambda _: body.is_displayed())

    yield _driver
    _driver.quit()
