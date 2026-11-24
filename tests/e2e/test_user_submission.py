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
                "//button[normalize-space()='Add author']"
                "/ancestor::div[contains(concat(' ', normalize-space(@class), ' '),"
                " ' field ')][1]",
            )
        )
    )
    creator_field.find_element(
        By.XPATH, ".//button[normalize-space()='Add author']"
    ).click()

    modal = wait.until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, ".ui.modal.active"))
    )
    wait.until(EC.visibility_of_element_located((By.ID, "person_or_org.family_name")))

    # The customised creator editor should not ask for a role
    assert modal.find_elements(By.XPATH, ".//label[normalize-space()='Role']") == []

    modal.find_element(By.ID, "person_or_org.family_name").send_keys("Example")
    modal.find_element(By.ID, "person_or_org.given_name").send_keys("User")
    modal.find_element(By.XPATH, ".//button[normalize-space()='Save']").click()

    wait.until(EC.invisibility_of_element_located(modal))
    wait.until(lambda _: "Example, User" in creator_field.text)


def test_contributor_customisation(driver):
    """Check contributor help text and adding a person with a role."""
    login(
        driver,
        DEPOSITOR_EMAIL,
        TEST_PASSWORD,
        next_url="/uploads/new",
    )
    wait = WebDriverWait(driver, timeout=10)

    help_text = (
        "Individuals or institutions, in addition to the creators, responsible "
        "for collecting, managing, distributing or other-wise contributing to "
        "the development of the resource."
    )
    wait.until(
        EC.visibility_of_element_located(
            (
                By.XPATH,
                f"//label[@class='helptext'][normalize-space(text())='{help_text}']",
            )
        )
    )

    contributor_field = wait.until(
        EC.visibility_of_element_located(
            (
                By.XPATH,
                "//button[normalize-space()='Add contributor']"
                "/ancestor::div[contains(concat(' ', normalize-space(@class), ' '),"
                " ' field ')][1]",
            )
        )
    )
    contributor_field.find_element(
        By.XPATH, ".//button[normalize-space()='Add contributor']"
    ).click()

    modal = wait.until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, ".ui.modal.active"))
    )
    wait.until(EC.visibility_of_element_located((By.ID, "person_or_org.family_name")))

    modal.find_element(By.ID, "person_or_org.family_name").send_keys("Example")
    modal.find_element(By.ID, "person_or_org.given_name").send_keys("User")

    # Saving without a role should be rejected and keep the modal open
    modal.find_element(By.XPATH, ".//button[normalize-space()='Save']").click()
    wait.until(
        lambda _: modal.find_elements(
            By.XPATH, ".//*[normalize-space()='Role is a required field.']"
        )
    )
    assert modal.is_displayed()

    # The customised contributor editor should ask for a role
    role_dropdown = modal.find_element(
        By.XPATH,
        ".//label[normalize-space()='Role']"
        "/following-sibling::div[contains(@class, 'dropdown')]",
    )
    role_dropdown.click()
    wait.until(
        EC.element_to_be_clickable(
            role_dropdown.find_element(
                By.XPATH, ".//div[@role='option'][normalize-space()='Data collector']"
            )
        )
    ).click()

    modal.find_element(By.XPATH, ".//button[normalize-space()='Save']").click()

    wait.until(EC.invisibility_of_element_located(modal))
    wait.until(lambda _: "Example, User" in contributor_field.text)
    assert "Data collector" in contributor_field.text

    # The edit modal decides separately whether to show the role, so check it too
    contributor_field.find_element(
        By.XPATH, ".//button[normalize-space()='Edit']"
    ).click()
    edit_modal = wait.until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, ".ui.modal.active"))
    )
    edit_role_dropdown = edit_modal.find_element(
        By.XPATH,
        ".//label[normalize-space()='Role']"
        "/following-sibling::div[contains(@class, 'dropdown')]",
    )
    assert "Data collector" in edit_role_dropdown.text

    edit_modal.find_element(By.XPATH, ".//button[normalize-space()='Cancel']").click()
    wait.until(EC.invisibility_of_element_located(edit_modal))
