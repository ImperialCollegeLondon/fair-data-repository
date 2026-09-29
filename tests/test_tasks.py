"""Tests for ic_data_repo.tasks."""

from io import BytesIO
from unittest.mock import patch

import pytest
from ic_data_repo.tasks import create_system_record_and_download_files
from invenio_access.permissions import system_identity
from invenio_rdm_records.proxies import current_rdm_records_service
from invenio_search.proxies import current_search


@pytest.fixture
def record_metadata():
    """Return metadata valid for publishing a dataset record."""
    return {
        "metadata": {
            "title": "System-created test dataset",
            "description": "A record created by a background task.",
            "resource_type": {"id": "dataset"},
            "publication_date": "2026-09-18",
            "creators": [
                {
                    "person_or_org": {
                        "type": "personal",
                        "given_name": "Test",
                        "family_name": "Creator",
                    }
                }
            ],
        },
        "files": {"enabled": True},
    }


@pytest.fixture(scope="module")
def app_config(app_config):
    """Disable the unrelated Symplectic publish integration."""
    app_config["SYMPLECTIC_ENABLED"] = False
    return app_config


def _get_created_record():
    """Read the sole record created by a test through the records service."""
    current_search.flush_and_refresh("*")
    results = current_rdm_records_service.search(system_identity)
    [record] = results.hits
    return current_rdm_records_service.read(system_identity, record["id"])


def test_create_system_record_publishes(
    location, record_metadata, search_clear, vocabularies
):
    """Test the task creates a published record through the RDM service."""
    record_metadata["files"]["enabled"] = False

    create_system_record_and_download_files(record_metadata, [])

    record = _get_created_record()

    assert record.data["status"] == "published"
    assert record.data["metadata"]["title"] == record_metadata["metadata"]["title"]


@patch("ic_data_repo.tasks.requests")
def test_create_system_record_downloads_and_publishes_files(
    mock_requests, location, record_metadata, search_clear, vocabularies
):
    """Test the task downloads, commits, and publishes supplied files."""
    file_content = b"column,value\nexample,42\n"
    file_name = "example.csv"
    file_url = "https://files.example.org/blah"
    mock_requests.get().__enter__().raw = BytesIO(file_content)

    create_system_record_and_download_files(record_metadata, [(file_name, file_url)])

    record = _get_created_record()
    files = current_rdm_records_service.files.list_files(system_identity, record.id)
    downloaded_file = current_rdm_records_service.files.get_file_content(
        system_identity, record.id, file_name
    )

    assert record.data["status"] == "published"
    assert [f["key"] for f in files.entries] == [file_name]
    with downloaded_file.open_stream("rb") as stream:
        assert stream.read() == file_content
    mock_requests.get.assert_called_with(file_url, stream=True)


def test_create_system_record_adds_to_community(
    location, record_metadata, search_clear, vocabularies
):
    """Test the task adds the created record to a specified community."""
    from invenio_communities.proxies import current_communities

    record_metadata["files"]["enabled"] = False

    community_slug = "test-community"
    current_communities.service.create(
        data=dict(
            slug=community_slug,
            metadata=dict(title="whatever"),
            access=dict(visibility="public"),
        ),
        identity=system_identity,
    )

    create_system_record_and_download_files(
        record_metadata, [], community=community_slug
    )

    record = _get_created_record()
    [record_community] = record.data["parent"]["communities"]["entries"]
    assert record_community["slug"] == community_slug
