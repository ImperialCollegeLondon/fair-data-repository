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

    allowed_license = "Creative Commons Attribution 4.0 International"
    restricted_license = "Creative Commons: Attribution + No Derivative Works 4.0"

    item_locator = (By.CSS_SELECTOR, ".deposit-listitem")
    remove_locator = (By.XPATH, ".//button[normalize-space()='Remove']")
    add_locator = (By.XPATH, ".//button[normalize-space()='Add license']")

    license_items = license_field.find_elements(*item_locator)
    assert len(license_items) == 1
    assert (
        license_items[0].find_element(By.CSS_SELECTOR, ".header").text
        == allowed_license
    )

    remove_buttons = license_field.find_elements(*remove_locator)
    assert len(remove_buttons) == 1
    assert remove_buttons[0].is_displayed()
    assert license_field.find_elements(*add_locator) == []

    remove_buttons[0].click()

    wait.until(lambda _: license_field.find_elements(*item_locator) == [])
    assert license_field.find_elements(*remove_locator) == []
    assert allowed_license not in license_field.text

    license_field.find_element(*add_locator).click()

    modal = wait.until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, ".ui.modal.active"))
    )

    wait.until(lambda _: allowed_license in modal.text)
    assert restricted_license not in modal.text

    modal.find_element(By.NAME, "cancel").click()
    wait.until(EC.invisibility_of_element_located(modal))

    assert license_field.find_elements(*item_locator) == []
    assert license_field.find_element(*add_locator).is_displayed()

    license_field.find_element(*add_locator).click()

    modal = wait.until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, ".ui.modal.active"))
    )

    license_option = wait.until(
        lambda _: modal.find_element(
            By.XPATH,
            ".//div[contains(concat(' ', normalize-space(@class), ' '),"
            " ' license-item ')]"
            f"[.//div[normalize-space()='{allowed_license}']]",
        )
    )
    wait.until(EC.element_to_be_clickable(license_option)).click()

    modal.find_element(By.NAME, "submit").click()
    wait.until(EC.invisibility_of_element_located(modal))

    wait.until(lambda _: len(license_field.find_elements(*item_locator)) == 1)

    license_item = license_field.find_element(*item_locator)
    assert license_item.is_displayed()
    assert license_item.find_element(By.CSS_SELECTOR, ".header").text == allowed_license

    remove_buttons = license_field.find_elements(*remove_locator)
    assert len(remove_buttons) == 1
    assert remove_buttons[0].is_displayed()
    assert license_field.find_elements(*add_locator) == []
