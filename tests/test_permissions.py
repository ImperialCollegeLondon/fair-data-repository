"""Tests for ic_data_repo.permissions."""

import pytest
from flask_principal import Identity, UserNeed
from ic_data_repo.permissions import (
    ALLOWED_JOB_FAMILIES,
    POSTGRADUATE_ROLE_TYPE,
    AbleToDeposit,
    AbleToSelectRestrictedLicense,
    ImperialRecordPermissionPolicy,
    deposit_action,
    restricted_license_action,
    user_is_allowed_employee,
    user_is_postgraduate,
)
from invenio_access.permissions import ActionUsers, system_identity
from invenio_records_permissions.generators import SystemProcess


def test_restricted_license_generator():
    """Test the restricted licence generator returns its named action need."""
    assert AbleToSelectRestrictedLicense().needs() == [restricted_license_action]


def test_deposit_generator():
    """Test the deposit generator returns its named action need."""
    assert AbleToDeposit().needs() == [deposit_action]


@pytest.mark.parametrize(
    "action_name,generator_class",
    [
        ("can_select_restricted_license", AbleToSelectRestrictedLicense),
        ("can_create", AbleToDeposit),
    ],
)
def test_deposit_permission_policy_generators(action_name, generator_class):
    """Test the permission policy returns the correct generators for actions."""
    custom_generator, system_process = getattr(
        ImperialRecordPermissionPolicy, action_name
    )
    assert isinstance(custom_generator, generator_class)
    assert isinstance(system_process, SystemProcess)


@pytest.mark.parametrize(
    "action_name,need",
    [
        ("select_restricted_license", restricted_license_action),
        ("create", deposit_action),
    ],
)
def test_permission_grant_and_revoke(action_name, need, db):
    """Test restricted licence access is independent of deposit access."""
    user_id = 2
    identity = Identity(user_id)
    identity.provides.add(UserNeed(user_id))

    assert not ImperialRecordPermissionPolicy(action_name).allows(
        identity
    ), f"{action_name} access should initially be denied"

    grant = ActionUsers.allow(need, user_id=user_id)
    db.session.add(grant)
    db.session.flush()

    assert ImperialRecordPermissionPolicy(action_name).allows(
        identity
    ), f"{action_name} grant should allow access"

    db.session.delete(grant)
    db.session.flush()

    assert not ImperialRecordPermissionPolicy(action_name).allows(
        identity
    ), f"removing the grant should revoke {action_name} access"


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
