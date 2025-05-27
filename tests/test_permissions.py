"""Tests for ic_data_repo.permissions."""

import pytest
from ic_data_repo.permissions import (
    ALLOWED_JOB_FAMILIES,
    POSTGRADUATE_ROLE_TYPE,
    user_is_allowed_employee,
    user_is_postgraduate,
)


@pytest.mark.parametrize(
    "role_type,expected",
    [(POSTGRADUATE_ROLE_TYPE, True), ("foobar", False), (None, False)],
)
def test_user_is_postgraduate(role_type, expected):
    """Test user_is_postgraduate."""
    assert user_is_postgraduate(role_type, None) == expected


def test_user_is_postgraduate_error():
    """Test user_is_postgraduate raises error for inconsistent data."""
    with pytest.raises(ValueError):
        user_is_postgraduate(POSTGRADUATE_ROLE_TYPE, "foobar")


@pytest.mark.parametrize(
    "job_family,expected",
    [(job_family, True) for job_family in ALLOWED_JOB_FAMILIES]
    + [("foobar", False), (None, False)],
)
def test_user_is_allowed_employee(job_family, expected):
    """Test user_is_allowed_employee."""
    assert user_is_allowed_employee(None, job_family) == expected


def test_user_is_allowed_employee_error():
    """Test user_is_allowed_employee raises error for inconsistent data."""
    with pytest.raises(ValueError):
        user_is_allowed_employee(POSTGRADUATE_ROLE_TYPE, ALLOWED_JOB_FAMILIES[0])
