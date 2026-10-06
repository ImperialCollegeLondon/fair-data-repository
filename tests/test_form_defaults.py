"""Tests for the deposit form defaults."""

import pytest
from flask_login import login_user
from ic_data_repo.config.utils import get_user_form_default
from invenio_accounts.models import UserIdentity

ORCID_ID = "0000-0002-1825-0097"


@pytest.fixture
def profile_user(UserFixture, app, db):
    """A user with a full name and an Imperial affiliation in their profile."""
    u = UserFixture(
        email="ada@imperial.ac.uk",
        password="password",
        user_profile={
            "full_name": "Lovelace, Ada",
            "affiliations": "Imperial College London",
        },
    )
    u.create(app, db)
    return u.user


def _expected_creator(**extra_person_or_org):
    return {
        "person_or_org": {
            "type": "personal",
            "name": "Lovelace, Ada",
            "given_name": "Ada",
            "family_name": "Lovelace",
            **extra_person_or_org,
        },
        "affiliations": [{"id": "041kmwe10"}],
    }


def test_creator_default_unlinked(app, profile_user):
    """An unlinked user's default creator has no identifiers."""
    with app.test_request_context():
        login_user(profile_user)
        creators = get_user_form_default()

    assert creators == [_expected_creator()]


def test_creator_default_linked_orcid(app, db, profile_user):
    """A linked user's default creator carries their stored ORCID iD."""
    UserIdentity.create(profile_user, "orcid", ORCID_ID)
    db.session.commit()

    with app.test_request_context():
        login_user(profile_user)
        creators = get_user_form_default()

    assert creators == [
        _expected_creator(identifiers=[{"scheme": "orcid", "identifier": ORCID_ID}])
    ]
