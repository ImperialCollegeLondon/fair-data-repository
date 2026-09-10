"""End-to-end tests for the frontpage using Selenium."""

import pytest

pytestmark = pytest.mark.e2e


def test_frontpage_branding(driver):
    """Test that the frontpage displays the correct branding."""
    page = driver.page_source
    assert "Helix" in page
    assert "Imperial College London's FAIR Data Repository" in page
