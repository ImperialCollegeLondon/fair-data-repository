"""End-to-end tests for the LimitedLicenseField customisation."""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from tests.e2e.conftest import DEPOSITOR_EMAIL, TEST_PASSWORD, login

pytestmark = pytest.mark.e2e


def test_limited_license_field(driver):
    """Check limited license field customisation."""
    login(
        driver,
        DEPOSITOR_EMAIL,
        TEST_PASSWORD,
        next_url="/uploads/new",
    )
    wait = WebDriverWait(driver, timeout=10)

    license_field = wait.until(
        EC.visibility_of_element_located(
            (
                By.XPATH,
                "//label[normalize-space()='Licenses']"
                "/ancestor::div[contains(concat(' ', normalize-space(@class), ' '),"
                " ' field ')][1]",
            )
        )
    )

    remove_locator = (By.XPATH, ".//button[normalize-space()='Remove']")
    while remove_buttons := license_field.find_elements(*remove_locator):
        previous_count = len(remove_buttons)
        remove_buttons[0].click()
        wait.until(
            lambda _: len(license_field.find_elements(*remove_locator)) < previous_count
        )

    license_field.find_element(
        By.XPATH, ".//button[normalize-space()='Add license']"
    ).click()

    modal = wait.until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, ".ui.modal.active"))
    )

    allowed_license = "Creative Commons Attribution 4.0 International"
    restricted_license = "Creative Commons: Attribution + No Derivative Works 4.0"

    wait.until(lambda _: allowed_license in modal.text)
    assert restricted_license not in modal.text

    modal.find_element(By.NAME, "cancel").click()
    wait.until(EC.invisibility_of_element_located(modal))

    assert license_field.find_elements(By.CSS_SELECTOR, ".deposit-listitem") == []
    assert license_field.find_element(
        By.XPATH, ".//button[normalize-space()='Add license']"
    ).is_displayed()
