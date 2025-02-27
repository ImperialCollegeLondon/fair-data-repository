"""Functions for obtaining Imperial users.

This is mostly so that we can obtain a list of potential collaborators, which we do by
filtering users by their role type.

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
"""

import asyncio
from dataclasses import dataclass
from typing import Any, AsyncIterable, Optional

from azure.identity.aio import ClientSecretCredential
from kiota_abstractions.base_request_configuration import RequestConfiguration
from msgraph import GraphServiceClient
from msgraph.generated.users.users_request_builder import UsersRequestBuilder

_POSSIBLE_CONTRIBUTOR_ROLES = {
    "Employee",
    "Ex-Employee",
    "Honorary",
    "Visiting Researcher",
    "Casual & Bursary",
    "Emeritus",
    "Sponsored Researcher",
}
"""The role types that we consider when searching for possible contributors."""

_ROLE_TYPE_ATTR_NAME = "onPremisesExtensionAttributes/extensionAttribute6"
"""The name of the attribute which contains the role type."""


@dataclass
class ImperialUser:
    """A user at Imperial College London."""

    username: str
    """The username, not including the @ic.ac.uk suffix."""
    full_name: str
    """The user's specified display name."""


def get_client(
    tenant_id: str, client_id: str, client_secret: str
) -> GraphServiceClient:
    """Get a client for interacting with the Microsoft Graph API."""
    credential = ClientSecretCredential(tenant_id, client_id, client_secret)
    return GraphServiceClient(credentials=credential)


async def get_imperial_users(
    client: GraphServiceClient, config: Optional[RequestConfiguration[Any]] = None
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
            # It seems unlikely that the returned users won't contain both a username
            # and a display name, but the type hints seem to suggest this is a
            # possibility, so we check for both
            username = user.user_principal_name
            if not username:
                continue
            username = username.removesuffix("@ic.ac.uk")

            full_name = user.display_name or username
            yield ImperialUser(username=username, full_name=full_name)

        # If there are more users left to retrieve, the API gives a link to get the next
        # 100
        if not users.odata_next_link:
            return
        users_request = client.users.with_url(users.odata_next_link)


async def get_possible_imperial_contributors(
    client: GraphServiceClient,
) -> AsyncIterable[ImperialUser]:
    """Get Imperial users who may be contributors based on their role type."""
    config = _get_request_config_for_roles(_POSSIBLE_CONTRIBUTOR_ROLES)
    async for user in get_imperial_users(client, config):
        yield user


def _get_request_config_for_roles(roles: set[str]) -> RequestConfiguration[Any]:
    """Get the configuration to select only the users we want.

    Note that we have to add the count parameter and the ConsistencyLevel header to make
    this work for some reason. See:
        https://stackoverflow.com/questions/49764678/microsoft-graph-filter-for-onpremisesextensionattributes
    """  # noqa: E501
    filter = " or ".join(f"{_ROLE_TYPE_ATTR_NAME} eq '{role}'" for role in roles)
    query_params = UsersRequestBuilder.UsersRequestBuilderGetQueryParameters(
        select=["displayName", "userPrincipalName"],
        filter=filter,
        count=True,
    )
    config = RequestConfiguration(
        query_parameters=query_params,
    )
    config.headers.add("ConsistencyLevel", "eventual")
    return config


if __name__ == "__main__":

    async def main():
        """Print out all the possible Imperial collaborators."""
        import os

        client_id = os.getenv("ICL_OAUTH_CLIENT_ID")
        client_secret = os.getenv("ICL_OAUTH_CLIENT_SECRET")
        tenant_id = "2b897507-ee8c-4575-830b-4f8267c3d307"
        client = get_client(tenant_id, client_id, client_secret)

        print("Possible Imperial contributors:")
        async for user in get_possible_imperial_contributors(client):
            print(f" - {user.full_name} ({user.username})")

    asyncio.run(main())
