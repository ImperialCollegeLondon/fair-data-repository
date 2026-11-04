"""End-to-end tests for user submission using Selenium."""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from tests.e2e.conftest import DEPOSITOR_EMAIL, TEST_PASSWORD, login

pytestmark = pytest.mark.e2e


def test_user_submission(submission_request_url):
    """Test that the user submission form redirects to requests page."""
    assert "/requests/" in submission_request_url


def test_creator_customisation(driver):
    """Check creator help text and adding a person without a role."""
    login(
        driver,
        DEPOSITOR_EMAIL,
        TEST_PASSWORD,
        next_url="/uploads/new?community=icl",
    )
    wait = WebDriverWait(driver, timeout=10)

    help_text = (
        "The main individuals or institutions involved in creating the data set."
    )
    wait.until(
        EC.visibility_of_element_located(
            (
                By.XPATH,
                f"//label[@class='helptext'][normalize-space(text())='{help_text}']",
            )
        )
    )

    creator_field = wait.until(
        EC.visibility_of_element_located(
            (
                By.XPATH,
                "//button[normalize-space()='Add creator']"
                "/ancestor::div[concat(' ', normalize-space(@class), ' '),"
                " ' field ')][1]",
            )
        )
    )
    creator_field.find_element(
        By.XPATH, ".//button[normalize-space()='Add creator']"
    ).click()

    modal = wait.until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, ".ui.modal.active"))
    )
    wait.until(EC.visibility_of_element_located((By.ID, "person_or_org.family_name")))

    assert modal.find_elements(By.XPATH, ".//label[normalize-space()='Role']") == []

    modal.find_element(By.ID, "person_or_org.family_name").send_keys("Example")
    modal.find_element(By.ID, "person_or_org.given_name").send_keys("User")
    modal.find_element(By.XPATH, ".//button[normalize-space()='Save']").click()

    wait.until(EC.invisibility_of_element_located(modal))
    wait.until(lambda _: "Example, Alex" in creator_field.text)
