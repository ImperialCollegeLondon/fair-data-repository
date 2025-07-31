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

from collections.abc import AsyncIterable

from azure.identity.aio import ClientSecretCredential
from kiota_abstractions.base_request_configuration import RequestConfiguration
from msgraph import GraphServiceClient
from msgraph.generated.models.user import User
from msgraph.generated.users.users_request_builder import UsersRequestBuilder

_QueryParameters = UsersRequestBuilder.UsersRequestBuilderGetQueryParameters


def get_client(
    tenant_id: str, client_id: str, client_secret: str
) -> GraphServiceClient:
    """Get a client for interacting with the Microsoft Graph API."""
    credential = ClientSecretCredential(tenant_id, client_id, client_secret)
    return GraphServiceClient(credentials=credential)


async def get_imperial_users(
    client: GraphServiceClient,
    config: RequestConfiguration[_QueryParameters] | None = None,
) -> AsyncIterable[User]:
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
            yield user

        # If there are more users left to retrieve, the API gives a link to get the next
        # 100
        if not users.odata_next_link:
            return
        users_request = client.users.with_url(users.odata_next_link)
