"""End-to-end tests for the FundingField customisation."""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from tests.e2e.conftest import DEPOSITOR_EMAIL, TEST_PASSWORD, login

pytestmark = pytest.mark.e2e


def test_funding_field(driver):
    """Check that the customised funding field opens both funding modals."""
    login(
        driver,
        DEPOSITOR_EMAIL,
        TEST_PASSWORD,
        next_url="/uploads/new?community=icl",
    )
    wait = WebDriverWait(driver, timeout=10)

    funding_field = wait.until(
        EC.visibility_of_element_located(
            (
                By.XPATH,
                "//label[normalize-space()='Awards/Grants']"
                "/ancestor::div[contains(concat(' ', normalize-space(@class), ' '),"
                " ' field ')][1]",
            )
        )
    )

    funding_field.find_element(
        By.XPATH, ".//button[normalize-space()='Add custom']"
    ).click()
    modal = wait.until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, ".ui.modal.active"))
    )
    assert modal.find_element(
        By.XPATH, ".//h2[normalize-space()='Add custom funding']"
    ).is_displayed()

    modal.find_element(By.XPATH, ".//button[normalize-space()='Cancel']").click()
    wait.until(EC.invisibility_of_element_located(modal))

    funding_field.find_element(By.XPATH, ".//button[normalize-space()='Add']").click()
    modal = wait.until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, ".ui.modal.active"))
    )
    assert modal.find_element(
        By.XPATH, ".//h2[normalize-space()='Add standard award/grant']"
    ).is_displayed()
