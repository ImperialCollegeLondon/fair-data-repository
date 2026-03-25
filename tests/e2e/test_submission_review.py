"""End-to-end tests for user submissio review using Selenium."""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from tests.e2e.conftest import ARTIFACTS_DIR, REVIEWER_EMAIL, TEST_PASSWORD, login

pytestmark = pytest.mark.e2e


def test_submission_review_accept(driver, submission_request_url):
    """Superuser can open and accept a submission request."""
    login(driver, REVIEWER_EMAIL, TEST_PASSWORD, "/communities/icl/requests/")
    WebDriverWait(driver, timeout=10).until(
        lambda d: d.current_url.endswith("/communities/icl/requests/")
    )

    driver.get(submission_request_url)
    WebDriverWait(driver, timeout=10).until(
        lambda d: d.current_url == submission_request_url
    )

    accept_locator = (By.XPATH, "//button[normalize-space()='Accept and publish']")
    accept_btn = WebDriverWait(driver, timeout=10).until(
        EC.element_to_be_clickable(accept_locator)
    )
    accept_btn.click()

    accept_modal = WebDriverWait(driver, timeout=10).until(
        EC.visibility_of_element_located((By.ID, "accept"))
    )
    confirm_accept_btn = WebDriverWait(driver, timeout=10).until(
        lambda d: accept_modal.find_element(
            By.XPATH, ".//button[normalize-space()='Accept and publish']"
        )
    )
    confirm_accept_btn.click()

    WebDriverWait(driver, timeout=10).until(
        lambda d: d.current_url == submission_request_url
    )

    # Check for accepted status
    status_container = WebDriverWait(driver, timeout=10).until(
        EC.visibility_of_element_located(
            (By.XPATH, "//h3[normalize-space()='Status']/following-sibling::div[1]")
        )
    )
    accepted_status = status_container.find_element(
        By.XPATH, ".//span[normalize-space()='Accepted']"
    )
    driver.get_full_page_screenshot_as_file(str(ARTIFACTS_DIR / "accepted_status.png"))
    assert accepted_status.is_displayed()
