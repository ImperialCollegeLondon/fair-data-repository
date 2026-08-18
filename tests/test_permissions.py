"""Tests for ic_data_repo.permissions."""

import pytest
from flask_principal import Identity, UserNeed
from ic_data_repo.permissions import (
    ALLOWED_JOB_FAMILIES,
    POSTGRADUATE_ROLE_TYPE,
    AbleToSelectRestrictedLicense,
    ImperialRecordPermissionPolicy,
    deposit_action,
    restricted_license_action,
    user_is_allowed_employee,
    user_is_postgraduate,
)
from invenio_access.permissions import ActionUsers, system_identity


def test_restricted_license_generator():
    """Test the restricted licence generator returns its named action need."""
    assert AbleToSelectRestrictedLicense().needs() == [restricted_license_action]


def test_restricted_license_permission_grant_and_revoke(user, db):
    """Test restricted licence access is independent of deposit access."""
    identity = Identity(user.user.id)
    identity.provides.add(UserNeed(user.user.id))

    assert not ImperialRecordPermissionPolicy("select_restricted_license").allows(
        identity
    ), "restricted licence access should initially be denied"
    assert not ImperialRecordPermissionPolicy("create").allows(
        identity
    ), "deposit access should initially be denied"

    restricted_license_grant = ActionUsers.allow(
        restricted_license_action, user_id=user.user.id
    )
    db.session.add(restricted_license_grant)
    db.session.flush()

    assert ImperialRecordPermissionPolicy("select_restricted_license").allows(
        identity
    ), "restricted licence grant should allow access"
    assert not ImperialRecordPermissionPolicy("create").allows(
        identity
    ), "restricted licence grant should not allow deposits"

    db.session.delete(restricted_license_grant)
    db.session.flush()

    assert not ImperialRecordPermissionPolicy("select_restricted_license").allows(
        identity
    ), "removing the grant should revoke restricted licence access"

    db.session.add(ActionUsers.allow(deposit_action, user_id=user.user.id))
    db.session.flush()

    assert ImperialRecordPermissionPolicy("create").allows(
        identity
    ), "deposit grant should allow deposits"
    assert not ImperialRecordPermissionPolicy("select_restricted_license").allows(
        identity
    ), "deposit grant should not allow restricted licence access"


def test_system_process_can_select_restricted_license():
    """Test system processes can select restricted licences."""
    assert ImperialRecordPermissionPolicy("select_restricted_license").allows(
        system_identity
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
