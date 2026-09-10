"""End-to-end tests for user submission using Selenium."""

import pytest

pytestmark = pytest.mark.e2e


def test_user_submission(submission_request_url):
    """Test that the user submission form redirects to requests page."""
    assert "/requests/" in submission_request_url
