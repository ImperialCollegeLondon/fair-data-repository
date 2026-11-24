"""End-to-end tests for the MandatoryPIDField customisation.

The upload form's DOI field is overridden by ``MandatoryPIDField`` (see
``site/ic_data_repo/assets/semantic-ui/js/ic_data_repo/MandatoryPIDField.js``).
Unlike the upstream field, the Imperial version always renders the DOI as a
required field and only offers a repository-minted ("managed") DOI, removing the
option for depositors to supply their own DOI.

DataCite must be enabled on the server, otherwise the DOI part of the deposit form will
be hidden.

You can do this by setting the ``INVENIO_DATACITE_ENABLED`` and
``INVENIO_DATACITE_PREFIX`` environment variables.
"""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from tests.e2e.conftest import DEPOSITOR_EMAIL, TEST_PASSWORD, login

pytestmark = pytest.mark.e2e


def test_doi_field_is_mandatory_and_managed_only(driver):
    """The DOI field is required and only offers a repository-minted DOI."""
    login(driver, DEPOSITOR_EMAIL, TEST_PASSWORD, next_url="/uploads/new")
    wait = WebDriverWait(driver, timeout=10)
    wait.until(lambda d: d.current_url.endswith("/uploads/new"))

    # The customised DOI field renders and its form field is marked required
    # (Semantic UI adds the `required` class, which draws the asterisk).
    wait.until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//div[contains(concat(' ', normalize-space(@class), ' '),"
                " ' required ')]"
                "[.//label[contains(normalize-space(),"
                " 'Digital Object Identifier')]]",
            )
        )
    )

    # Only the repository-managed "reserve" action is offered.
    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//button[normalize-space()='Get a DOI now!']")
        )
    )

    # The upstream "bring your own DOI" controls are removed by the
    # customisation: there is no managed/unmanaged radio switch...
    assert (
        driver.find_elements(
            By.XPATH, "//*[contains(normalize-space(), 'Yes, I already have one')]"
        )
        == []
    )
    # ...and no free-text input to paste an existing DOI.
    assert (
        driver.find_elements(
            By.CSS_SELECTOR, "input[placeholder*='Copy/paste your existing']"
        )
        == []
    )
