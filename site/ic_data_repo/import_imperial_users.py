"""Functions for obtaining Imperial users.

This is mostly so that we can obtain a list of potential collaborators, which we do by
filtering users by their role type and job family.

The current list of possible role types is:

- Employee
- Research Postgraduate
- Alumni (Taught Postgraduate)
- Undergraduate
- Honorary
- Casual & Bursary
- Alumni (Research Postgraduate)
- Taught Postgraduate
- Alumni (Undergraduate)
- Casual
- Visiting Researcher
- Academic Visitor (CWK)
- Contingent Worker
- Ex-Employee
- MRC Employees
- Emeritus
- System
- Contractor
- Role
- Sponsored Researcher
- MRC Employees (CWK)
- External
- Staff

The current list of possible job families is:

- Honorary Academics
- Professional Services
- Academic & Research
- Visiting Researcher
- Learning & Teaching
- Technical Services
- Operational Services
- Clinical Academic
- Non Staff
- Clinical Research
- NHS Nurses
- Academic Visitors

There are also many users with no job family specified.
"""

import asyncio
import logging
import subprocess as sp
from dataclasses import dataclass
from logging import Logger
from pathlib import Path
from shutil import which
from typing import Any, AsyncIterable, Iterable, Optional

import yaml
from azure.identity.aio import ClientSecretCredential
from kiota_abstractions.base_request_configuration import RequestConfiguration
from msgraph import GraphServiceClient
from msgraph.generated.users.users_request_builder import UsersRequestBuilder

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

_NAMES_VOCAB_PATH = (
    Path(__file__).parent.parent.parent / "app_data" / "imperial-names-vocab.yaml"
)
"""The path to the names vocab config file.

This config file is just needed to tell the `invenio` program that the input is in YAML
format and coming from /dev/stdin.
"""

_ICL_ROR_ID = "041kmwe10"
"""The ROR identifier for Imperial."""

_QueryParameters = UsersRequestBuilder.UsersRequestBuilderGetQueryParameters


def _get_default_logger() -> Logger:
    """Get a default logger for this module which just prints to stdout."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    return logger


@dataclass
class ImperialUser:
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


def get_client(
    tenant_id: str, client_id: str, client_secret: str
) -> GraphServiceClient:
    """Get a client for interacting with the Microsoft Graph API."""
    credential = ClientSecretCredential(tenant_id, client_id, client_secret)
    return GraphServiceClient(credentials=credential)


async def get_imperial_users(
    client: GraphServiceClient,
    config: Optional[RequestConfiguration[_QueryParameters]] = None,
) -> AsyncIterable[ImperialUser]:
    """Get Imperial users.

    By default, this function will return all Imperial users, but you can modify this
    with the config argument.
    """
    users_request = client.users
    while True:
        # Retrieve some more users from the API (maximum 100)
        users = await users_request.get(config)
        if not users or not users.value:
            return

        for user in users.value:
            # It seems unlikely that the returned users won't contain a username as well
            # as first and last names, but the type hints seem to suggest this is a
            # possibility, so let's check it
            username = user.user_principal_name
            if not username or not user.given_name or not user.surname:
                continue
            username = username.removesuffix("@ic.ac.uk")

            yield ImperialUser(
                username=username, given_name=user.given_name, family_name=user.surname
            )

        # If there are more users left to retrieve, the API gives a link to get the next
        # 100
        if not users.odata_next_link:
            return
        users_request = client.users.with_url(users.odata_next_link)


async def get_possible_imperial_contributors(
    client: GraphServiceClient, max_count: Optional[int] = None
) -> list[ImperialUser]:
    """Get Imperial users who may be contributors based on their role type."""
    config = _get_request_config_for_roles(
        _POSSIBLE_CONTRIBUTOR_INCLUDE_ROLE_TYPES,
        _POSSIBLE_CONTRIBUTOR_EXCLUDE_JOB_FAMILIES,
    )

    users = []
    async for user in get_imperial_users(client, config):
        users.append(user)

        if max_count is not None and len(users) == max_count:
            break
    return users


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


def import_imperial_contributors_to_invenio(
    client: GraphServiceClient,
    logger: Logger = _get_default_logger(),
    max_count: Optional[int] = None,
) -> None:
    """Import Imperial users which are possible contributors into the names vocab."""
    logger.info("Importing Imperial users...")
    users = asyncio.run(get_possible_imperial_contributors(client, max_count))
    logger.info(f"Loaded {len(users)} possible contributors.")

    logger.info("Adding names to Invenio")
    _add_names_to_invenio(users, logger)
    logger.info("Added names.")


def _get_invenio_path() -> str:
    """Get the path to the Invenio command-line tool."""
    path = which("invenio")
    if not path:
        raise RuntimeError("Could not find path to invenio program")
    return path


def _add_names_to_invenio(users: list[ImperialUser], logger: Logger):
    """Add the specified Imperial users to the names vocab."""
    # Path to invenio program
    invenio_path = _get_invenio_path()

    # Pass in names YAML via stdin
    names_str = yaml.dump(
        list(user.as_invenio_record() for user in users), sort_keys=False
    )
    process = sp.Popen(
        [
            invenio_path,
            "vocabularies",
            "import",
            "--vocabulary",
            "names",
            "--filepath",
            str(_NAMES_VOCAB_PATH),
        ],
        stdin=sp.PIPE,
        stdout=sp.PIPE,
        stderr=sp.STDOUT,
        text=True,
    )

    # Print contents of stdout and stderr with logger
    stdout = process.communicate(names_str)[0]
    for line in stdout.splitlines():
        logger.info(f"invenio: {line}")

    if process.returncode != 0:
        raise RuntimeError(f"invenio process exited with code {process.returncode}")
