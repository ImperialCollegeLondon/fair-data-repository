"""End-to-end tests for the force community feature."""

import json

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from tests.e2e.conftest import DEPOSITOR_EMAIL, TEST_PASSWORD, login

pytestmark = pytest.mark.e2e


def test_force_community_in_ui(driver):
    """UI review fields are pre-populated in new draft."""
    login(driver, DEPOSITOR_EMAIL, TEST_PASSWORD, "/uploads/new")
    WebDriverWait(driver, 10).until(lambda d: d.current_url.endswith("/uploads/new"))

    # Get the Imperial comminity data.
    icl = driver.execute_script("""
        return fetch("/api/communities/icl")
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                return response.json();
            });
    """)

    # Check that community review fields are overrided.
    data_element = driver.find_element(By.ID, "deposits-record")
    data = json.loads(data_element.get_property("value"))
    assert data["parent"]["review"] == {
        "type": "community-submission",
        "receiver": {"community": icl["id"]},
    }
    assert data["expanded"]["parent"]["review"]["receiver"]["id"] == icl["id"]
