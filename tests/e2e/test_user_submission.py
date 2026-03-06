"""End-to-end tests for user submission using Selenium."""

from pathlib import Path

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

pytestmark = pytest.mark.e2e


def test_user_submission(driver, tmp_path):
    """Test that the user submission form redirects to requests page."""
    # Navigate to login page and log in the test user
    driver.get(f"{pytest.base_url}/login/?next=%2Fuploads%2Fnew%3Fcommunity%3Dicl")
    driver.find_element(By.ID, "email").send_keys("test.user@test.co")
    driver.find_element(By.ID, "password").send_keys("password")
    driver.find_element(By.XPATH, "//button[normalize-space()='Log in']").click()

    # Wait for the page to load and check the URL
    WebDriverWait(driver, timeout=10).until(
        lambda d: d.current_url.endswith("uploads/new?community=icl")
    )
    assert driver.current_url.endswith("uploads/new?community=icl")

    # Fill in the required submission form elements
    driver.find_element(By.ID, "metadata.title").send_keys("Test Submission")
    driver.find_element(By.ID, "metadata.description").send_keys(
        "This is a test submission."
    )

    # Open the "Add creator" form and fill the "family name" field
    driver.find_element(By.XPATH, "//button[normalize-space()='Add creator']").click()
    WebDriverWait(driver, timeout=10).until(
        lambda d: d.find_element(By.ID, "person_or_org.family_name").is_displayed()
    )
    driver.find_element(By.ID, "person_or_org.family_name").send_keys("Test")
    driver.find_element(By.XPATH, "//button[normalize-space()='Save']").click()

    # Add a dummy file using the "Upload files" button
    dummy_file_path = (Path(__file__).parent / "fixtures/dummy_file.txt").resolve()

    file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
    file_input.send_keys(str(dummy_file_path))

    # Wait until submit button is truly enabled (not just present)
    submit_locator = (By.XPATH, "//button[normalize-space()='Submit for review']")

    WebDriverWait(driver, timeout=60).until(
        lambda d: (
            (btn := d.find_element(*submit_locator)).is_displayed()
            and btn.is_enabled()
            and (btn.get_attribute("disabled") is None)
        )
    )

    driver.find_element(*submit_locator).click()

    required_checkbox_names = [
        "acceptAccessToRecord",
        "acceptAfterPublishRecord",
        "acceptDepositAgreement",
    ]

    for name in required_checkbox_names:
        checkbox = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, f"input[type='checkbox'][name='{name}']")
            )
        )
        if not checkbox.is_selected():
            driver.execute_script("arguments[0].click();", checkbox)

    final_submit_btn = WebDriverWait(driver, timeout=20).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[normalize-space()='Submit record for review']")
        )
    )
    final_submit_btn.click()

    WebDriverWait(driver, timeout=10).until(lambda d: "/requests/" in d.current_url)
    assert "/requests/" in driver.current_url
