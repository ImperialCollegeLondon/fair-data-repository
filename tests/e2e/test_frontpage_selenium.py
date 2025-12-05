"""End-to-end tests for the frontpage using Selenium."""

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

BASE_URL = "https://127.0.0.1:5000"


@pytest.fixture
def driver():
    """Selenium WebDriver fixture."""
    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    _driver = webdriver.Firefox(options=options)
    _driver.get(BASE_URL)

    body = _driver.find_element(By.TAG_NAME, "body")
    wait = WebDriverWait(_driver, timeout=10)
    wait.until(lambda _: body.is_displayed())

    yield _driver
    _driver.quit()


def test_frontpage_branding(driver):
    """Test that the frontpage displays the correct branding."""
    page = driver.page_source
    assert "Helix" in page
    assert "Imperial College London's FAIR Data Repository" in page


def test_click_my_dashboard_link(driver):
    """Test that clicking the 'My Dashboard' link navigates to the dashboard."""
    links = driver.find_elements(By.TAG_NAME, "a")
    target = None
    for a in links:
        text = (a.text or "").strip()
        if text.lower() == "my dashboard":
            target = a
            break
    target.click()

    def is_dashboard_url(d):
        u = d.current_url or ""
        return "/me/uploads" in u or "me%2Fuploads" in u

    WebDriverWait(driver, 5).until(is_dashboard_url)
    assert is_dashboard_url(driver)
