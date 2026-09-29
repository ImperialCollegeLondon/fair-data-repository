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
    accepted_status = WebDriverWait(driver, timeout=10).until(
        EC.visibility_of_element_located(
            (
                By.XPATH,
                "//h3[normalize-space()='Status']/following-sibling::div[1]"
                "//span[normalize-space()='Accepted']",
            )
        )
    )
    driver.get_full_page_screenshot_as_file(str(ARTIFACTS_DIR / "accepted_status.png"))
    assert accepted_status is not None


def test_submission_review_decline(driver, submission_request_url):
    """Superuser can open and decline a submission request."""
    login(driver, REVIEWER_EMAIL, TEST_PASSWORD, "/communities/icl/requests/")
    WebDriverWait(driver, timeout=10).until(
        lambda d: d.current_url.endswith("/communities/icl/requests/")
    )

    driver.get(submission_request_url)
    WebDriverWait(driver, timeout=10).until(
        lambda d: d.current_url == submission_request_url
    )

    decline_locator = (By.XPATH, "//button[normalize-space()='Decline']")
    decline_btn = WebDriverWait(driver, timeout=10).until(
        EC.element_to_be_clickable(decline_locator)
    )
    decline_btn.click()

    decline_modal = WebDriverWait(driver, timeout=10).until(
        EC.visibility_of_element_located((By.ID, "decline"))
    )
    confirm_decline_btn = WebDriverWait(driver, timeout=10).until(
        lambda d: decline_modal.find_element(
            By.XPATH, ".//button[normalize-space()='Decline']"
        )
    )
    confirm_decline_btn.click()

    WebDriverWait(driver, timeout=10).until(
        lambda d: d.current_url == submission_request_url
    )

    # Check for declined status
    declined_status = WebDriverWait(driver, timeout=10).until(
        EC.visibility_of_element_located(
            (
                By.XPATH,
                "//h3[normalize-space()='Status']/following-sibling::div[1]"
                "//span[normalize-space()='Declined']",
            )
        )
    )
    driver.get_full_page_screenshot_as_file(str(ARTIFACTS_DIR / "declined_status.png"))
    assert declined_status is not None
