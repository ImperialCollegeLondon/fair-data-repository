"""Import custom data into vocabularies."""

import asyncio
import logging
import subprocess as sp
from abc import ABC, abstractmethod
from collections.abc import Iterable
from csv import DictReader
from dataclasses import dataclass
from datetime import datetime
from logging import Logger
from pathlib import Path
from shutil import which
from typing import Any

import yaml
from flask import current_app
from invenio_vocabularies.datastreams.factories import DataStreamFactory
from kiota_abstractions.base_request_configuration import RequestConfiguration
from msgraph import GraphServiceClient
from msgraph.generated.users.users_request_builder import UsersRequestBuilder

from .microsoft_graph_api_client import get_imperial_users

_POSSIBLE_CONTRIBUTOR_INCLUDE_ROLE_TYPES = {
    "Employee",
    "Ex-Employee",
    "Research Postgraduate",
    "Honorary",
    "Visiting Researcher",
    "Casual & Bursary",
    "Emeritus",
    "Sponsored Researcher",
    "MRC Employees",
    "MRC Employees (CWK)",
}
"""The role types that we consider when searching for possible contributors."""

_POSSIBLE_CONTRIBUTOR_EXCLUDE_JOB_FAMILIES = {
    "Professional Services",
    "Technical Services",
    "Operational Services",
    "NHS Nurses",
}
"""The job families to *exclude* from possible contributors."""

_ROLE_TYPE_ATTR_NAME = "onPremisesExtensionAttributes/extensionAttribute6"
"""The name of the attribute which contains the role type."""

_JOB_FAMILY_ATTR_NAME = "onPremisesExtensionAttributes/extensionAttribute14"
"""The name of the attribute which contains the job family."""

_VOCAB_CONFIG_PATH = (
    Path(__file__).parent.parent.parent / "app_data" / "vocabularies-import.yaml"
)
"""The path to the names vocab config file.

This config file is just needed to tell the `invenio` program that the input is in YAML
format and coming from /dev/stdin.
"""

_ICL_ROR_ID = "041kmwe10"
"""The ROR identifier for Imperial."""

_QueryParameters = UsersRequestBuilder.UsersRequestBuilderGetQueryParameters

_AWARD_ENDDATE_CUTOFF = datetime(year=2020, month=1, day=1)
"""Cutoff date applied to award end dates."""

_ICIS_FUNDER_ROR_MAP = {
    "Engineering & Physical Science Research Council (E": "0439y7842",
    "The Royal Society": "03wnrjx87",
    "Medical Research Council (MRC)": "03x94j517",
    "Imperial College Healthcare NHS Trust": "056ffv270",
    "National Institute for Health Research": "0187kwz08",
    "Wellcome Trust": "029chgv08",
    "Commission of the European Communities": "00k4n6c32",
    "British Heart Foundation": "02wdwnk04",
    "Cancer Research UK": "054225q67",
    "Biotechnology and Biological Sciences Research Cou": "00cwqg982",
    "Science and Technology Facilities Council (STFC)": "057g20z61",
    "Innovate UK": "05ar5fy68",
    "Natural Environment Research Council (NERC)": "02b5d8509",
    "Rosetrees Trust": "04e3zg361",
    "UK Research and Innovation": "001aqnf71",
    "The Leverhulme Trust": "012mzw131",
    "National Institutes of Health": "01cwqze88",
    "Engineering & Physical Sciences Research Council": "0439y7842",
    "Bill & Melinda Gates Foundation": "0456r8d26",
    "UK DRI Ltd": "02wedp412",
    "Defence Science and Technology Laboratory (DSTL)": "04jswqb94",
    "The Academy of Medical Sciences": "00c489v88",
    "The Faraday Institution": "05dt4bt98",
}
"""A mapping between funder names as recorded in ICIS and ROR identifiers."""


def _get_default_logger() -> Logger:
    """Get a default logger for this module which just prints to stdout."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    if not logger.hasHandlers():
        # Prevent multiple handlers from being added if function called multiple times
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        logger.addHandler(ch)
    return logger


class InvenioVocabEntry(ABC):
    """Base class for dataclasses that can be serialised as Invenio vocab entries."""

    @abstractmethod
    def as_invenio_record(self) -> dict[str, Any]:
        """Serialisation method."""
        pass


@dataclass
class ImperialUser(InvenioVocabEntry):
    """A user at Imperial College London."""

    username: str
    """The username, not including the @ic.ac.uk suffix."""
    given_name: str
    """The user's first name."""
    family_name: str
    """The user's last name."""

    def __str__(self) -> str:
        """Format as string."""
        return f"{self.family_name}, {self.given_name} ({self.username})"

    def as_invenio_record(self) -> dict[str, Any]:
        """Get this user in the form expected by the Invenio names vocabulary."""
        return {
            "family_name": self.family_name,
            "given_name": self.given_name,
            "id": self.username,
            "affiliations": [{"id": _ICL_ROR_ID}],
        }


@dataclass
class Award(InvenioVocabEntry):
    """A grant awarded to Imperial staff."""

    imperial_id: str
    """The internal Imperial ID for an award."""
    funder_id: str
    """The ID used by the funder for an award."""
    title: str
    """The title of the award."""
    funder_org_id: dict[str, str]
    """An identifier for the funding organisation."""

    def as_invenio_record(self) -> dict[str, Any]:
        """Get this award in the form expected by the Invenio awards vocabulary."""
        return dict(
            id=self.imperial_id,
            number=self.funder_id,
            title=dict(en=self.title),
            funder=self.funder_org_id,
        )


def _filter_expr_in_set(attr_name: str, possible_values: Iterable[str]) -> str:
    """Create a $filter expression to check for an attribute in some values.

    >>> _filter_expr_in_set("my_attr", ["a", "b"])
    "my_attr in ('a', 'b')"
    """
    set_str = ", ".join(f"'{value}'" for value in possible_values)
    return f"{attr_name} in ({set_str})"


def _get_request_config_for_roles(
    include_role_types: set[str], exclude_job_families: set[str]
) -> RequestConfiguration[_QueryParameters]:
    """Get the configuration to select only the users we want.

    Note that we have to add the count parameter and the ConsistencyLevel header to make
    this work for some reason. See:
        https://stackoverflow.com/questions/49764678/microsoft-graph-filter-for-onpremisesextensionattributes
    """  # noqa: E501
    # Include only some role types and exclude certain job families
    role_type_filter = _filter_expr_in_set(_ROLE_TYPE_ATTR_NAME, include_role_types)
    job_family_filter = (
        f"not {_filter_expr_in_set(_JOB_FAMILY_ATTR_NAME, exclude_job_families)}"
    )
    filter = f"{role_type_filter} and {job_family_filter}"

    query_params = _QueryParameters(
        select=["givenName", "surname", "userPrincipalName"],
        filter=filter,
        count=True,
    )
    config = RequestConfiguration(
        query_parameters=query_params,
    )
    config.headers.add("ConsistencyLevel", "eventual")
    return config


async def get_possible_imperial_contributors(
    client: GraphServiceClient, max_count: int | None = None
) -> list[ImperialUser]:
    """Get Imperial users who may be contributors based on their role type."""
    config = _get_request_config_for_roles(
        _POSSIBLE_CONTRIBUTOR_INCLUDE_ROLE_TYPES,
        _POSSIBLE_CONTRIBUTOR_EXCLUDE_JOB_FAMILIES,
    )

    users = []
    async for user in get_imperial_users(client, config):
        # It seems unlikely that the returned users won't contain a username as well
        # as first and last names, but the type hints seem to suggest this is a
        # possibility, so let's check it
        if not user.user_principal_name or not user.given_name or not user.surname:
            continue

        users.append(
            ImperialUser(
                username=user.user_principal_name.removesuffix("@ic.ac.uk"),
                given_name=user.given_name,
                family_name=user.surname,
            )
        )

        if max_count is not None and len(users) == max_count:
            break
    return users


def _get_invenio_path() -> str:
    """Get the path to the Invenio command-line tool."""
    path = which("invenio")
    if not path:
        raise RuntimeError("Could not find path to invenio program")
    return path


def import_imperial_contributors_to_invenio(
    client: GraphServiceClient,
    logger: Logger = _get_default_logger(),
    max_count: int | None = None,
) -> None:
    """Import Imperial users which are possible contributors into the names vocab."""
    logger.info("Importing Imperial users...")
    users = asyncio.run(get_possible_imperial_contributors(client, max_count))
    logger.info(f"Loaded {len(users)} possible contributors.")

    logger.info("Adding names to Invenio")
    _add_entries_to_vocab("names", users, logger)
    logger.info("Added names.")


def _add_entries_to_vocab(
    vocabulary_name: str, entries: Iterable[InvenioVocabEntry], logger: Logger
):
    """Add the specified Imperial users to the names vocab."""
    # Path to invenio program
    invenio_path = _get_invenio_path()

    # Pass in names YAML via stdin
    entries_str = yaml.dump(
        list(entry.as_invenio_record() for entry in entries), sort_keys=False
    )
    process = sp.Popen(
        [
            invenio_path,
            "vocabularies",
            "import",
            "--vocabulary",
            vocabulary_name,
            "--filepath",
            str(_VOCAB_CONFIG_PATH),
        ],
        stdin=sp.PIPE,
        stdout=sp.PIPE,
        stderr=sp.STDOUT,
        text=True,
    )

    # Print contents of stdout and stderr with logger
    stdout = process.communicate(entries_str)[0]
    for line in stdout.splitlines():
        logger.info(f"invenio: {line}")

    if process.returncode != 0:
        raise RuntimeError(f"invenio process exited with code {process.returncode}")


def _convert_award_datetime(date: str):
    """Convert ICIS date format strings to datetimes.

    Where a date is not provided (i.e. empty string) return datetime.min on the basis
    that it will be excluded by the date filtering.
    """
    try:
        return datetime.strptime(date, "%d-%b-%y")
    except ValueError:
        return datetime.min


def _get_funder_org_id(row: dict[str, str]) -> dict[str, str] | None:
    """Get a funder ROR from a row of ICIS data.

    Takes a conservative approach still not clear on how some data is structured in
    ICIS. May return the funder name 'Industry' or a funder id from a manually curated
    set of mapped ROR values. Returns None if there is ambiguity in the data or the
    funder is not part of the manually curated set.
    """
    funder = row["Funder"]
    sponsor = row["SPONSOR"]
    if funder == "Industry":
        return dict(name=funder)
    if funder != sponsor:
        return None
    try:
        return dict(id=_ICIS_FUNDER_ROR_MAP[funder])
    except KeyError:
        return None


def _process_icis_csv(filepath: Path):
    with open(filepath) as f:
        all_data = list(DictReader(f))

    uniq_awards: dict[str, dict[str, str]] = {}
    for row in all_data:
        uniq_awards.setdefault(row["AwardNumber"], row)

    date_filtered_awards = [
        val
        for val in uniq_awards.values()
        if _convert_award_datetime(val["AwardEndDate"]) > _AWARD_ENDDATE_CUTOFF
    ]

    awards = []
    for row in date_filtered_awards:
        if not (funder_org_id := _get_funder_org_id(row)):
            continue
        awards.append(
            Award(
                imperial_id=row["AwardNumber"],
                funder_id=row["Award Funder Reference"],
                title=row["AwardShortTitle"],
                funder_org_id=funder_org_id,
            )
        )
    return awards


def import_imperial_awards_to_invenio(
    award_data_file: Path, logger: Logger = _get_default_logger()
):
    """Import Imperial awards data into the awards vocabulary."""
    awards = _process_icis_csv(award_data_file)
    _add_entries_to_vocab("awards", awards, logger)


class VocabularyImportError(Exception):
    """Exception for errors occuring during vocab import."""


def import_to_vocabulary(datastream_config: dict[str, Any], allow_errors: bool = True):
    """Add data to a vocabulary via datastream."""
    ds = DataStreamFactory.create(
        readers_config=datastream_config["readers"],
        transformers_config=datastream_config.get("transformers"),
        writers_config=datastream_config["writers"],
    )
    errors = False
    for entry in ds.process():
        if entry.errors:
            current_app.logger.warning(str(entry.errors))
            errors = True

    if errors and not allow_errors:
        raise VocabularyImportError(
            "Unexpected errors encountered whilst importing vocabulary. "
            "See log for details."
        )
