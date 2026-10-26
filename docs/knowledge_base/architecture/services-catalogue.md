# Services Catalogue

> Reference of all built-in InvenioRDM services, their proxies, and responsibilities.

**Prerequisites:** [Service Layer](service-layer.md) **Related:**
[Architecture Overview](overview.md), [Permissions](../customisation/permissions.md)

## Records (`invenio-rdm-records`)

| Service                   | Proxy                                             | Purpose                                                                                    |
| ------------------------- | ------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| `RDMRecordService`        | `current_rdm_records_service`                     | Core CRUD for records and drafts (create, read, update, delete, publish, search, versions) |
| `RecordAccessService`     | via `current_rdm_records.access_service`          | Manage access links, grants, and embargo                                                   |
| File services             | via `current_rdm_records.records_service.files`   | Upload/download/delete files attached to records/drafts                                    |
| Media files service       | `current_rdm_records_media_files_service`         | Manage media files (e.g. IIIF images)                                                      |
| `RecordRequestsService`   | via `current_rdm_records.record_requests_service` | Requests scoped to a record (access requests, etc.)                                        |
| `CommunityRecordsService` | `current_community_records_service`               | Manage records belonging to a community                                                    |
| `IIIFService`             | via `current_rdm_records.iiif_service`            | IIIF image/presentation API                                                                |
| OAI-PMH service           | `current_oaipmh_server_service`                   | OAI-PMH harvesting endpoint sets                                                           |
| Storage service           | `current_rdm_records_storage_service`             | Low-level storage operations                                                               |

**Module:** `invenio_rdm_records.services` **Config:** `RDMRecordServiceConfig` (the
largest config — defines components, permissions, schemas, search options)

## Communities (`invenio-communities`)

| Service            | Purpose                                                        |
| ------------------ | -------------------------------------------------------------- |
| `CommunityService` | CRUD for communities (create, update, delete, search, feature) |
| `MembersService`   | Manage community members, invitations, roles                   |

**Module:** `invenio_communities.communities.services` **Proxy:**
`current_communities.service`

## Requests (`invenio-requests`)

| Service                        | Purpose                                                           |
| ------------------------------ | ----------------------------------------------------------------- |
| `RequestsService`              | Create/action workflow requests (submit, accept, decline, cancel) |
| `RequestEventsService`         | Timeline events/comments on requests                              |
| `UserModerationRequestService` | User moderation workflow                                          |

**Module:** `invenio_requests.services` **Proxy:** `current_requests_service`

## Vocabularies (`invenio-vocabularies`)

| Service               | Purpose                                                                          |
| --------------------- | -------------------------------------------------------------------------------- |
| `VocabulariesService` | CRUD for controlled vocabulary terms (subjects, resource types, languages, etc.) |

**Module:** `invenio_vocabularies.services` **Proxy:** `current_service` (from
`invenio_vocabularies.proxies`)

## Users (`invenio-users-resources`)

| Service          | Purpose                      |
| ---------------- | ---------------------------- |
| `UsersService`   | Search/read user profiles    |
| `GroupsService`  | Manage user groups/roles     |
| `DomainsService` | Manage email domain policies |

**Module:** `invenio_users_resources.services` **Proxy:** `current_users_service`

## Accessing Services

All services are available via Flask extension proxies:

```python
from invenio_rdm_records.proxies import current_rdm_records_service
from invenio_communities.proxies import current_communities
from invenio_requests.proxies import current_requests_service

# Use with an identity
result = current_rdm_records_service.read(identity, id_)
```

For system-level operations (background tasks, CLI commands):

```python
from invenio_access.permissions import system_identity

result = current_rdm_records_service.publish(system_identity, id_)
```

## Import Patterns

```python
# The extension object (gives access to all sub-services)
from invenio_rdm_records.proxies import current_rdm_records

# Specific service shortcuts
current_rdm_records.records_service  # RDMRecordService
current_rdm_records.access_service  # RecordAccessService
current_rdm_records.record_requests_service
current_rdm_records.community_records_service
current_rdm_records.iiif_service
current_rdm_records.oaipmh_server_service
current_rdm_records.storage_service
```
