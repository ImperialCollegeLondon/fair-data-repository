# Service Workflows

> Step-by-step examples of common InvenioRDM workflows using the service layer, showing
> how services interact.

**Prerequisites:** [Service Layer](../architecture/service-layer.md),
[Services Catalogue](../architecture/services-catalogue.md) **Related:**
[Permissions](permissions.md), [Custom Fields](custom-fields.md)

## Setup (Common to All Workflows)

```python
from invenio_access.permissions import system_identity
from invenio_rdm_records.proxies import current_rdm_records_service

service = current_rdm_records_service
```

For user-context operations (e.g. in a view or Celery task with user info):

```python
from flask import g
identity = g.identity  # or construct from user
```

## Workflow 1: Create and Publish a Record (Direct)

This is the simplest path — no community review required.

```python
# 1. Create a draft
draft = service.create(identity, data={
    "metadata": {
        "title": "My Dataset",
        "resource_type": {"id": "dataset"},
        "creators": [{"person_or_org": {"family_name": "Smith", "given_name": "John", "type": "personal"}}],
        "publication_date": "2024-01-15",
        "publisher": "Imperial College London",
    },
    "access": {
        "record": "public",
        "files": "public",
    },
    "files": {"enabled": True},
})
draft_id = draft.id

# 2. Upload files (three-step process)
# 2a. Initialize file entry (declares intent to upload)
service.draft_files.init_files(identity, draft_id, data=[
    {"key": "data.csv"},  # filename
])

# 2b. Upload file content
from io import BytesIO
content = BytesIO(b"col1,col2\n1,2\n")
service.draft_files.set_file_content(identity, draft_id, "data.csv", content)

# 2c. Commit the file (finalises upload, calculates checksum)
service.draft_files.commit_file(identity, draft_id, "data.csv")

# 3. Publish
record = service.publish(identity, draft_id)
print(record.id)  # the published record PID
```

**Permissions required:** `can_create`, `can_draft_create_files`, `can_publish`

## Workflow 2: Submit to Community with Review

When `RDM_COMMUNITY_REQUIRED_TO_PUBLISH = True` or when you want community curation
before publishing.

```python
from invenio_rdm_records.proxies import current_rdm_records

# 1. Create draft (same as above)
draft = service.create(identity, data={...})
draft_id = draft.id

# 2. Upload files (same as above)
# ...

# 3. Create a review request (associates draft with community)
review_service = current_rdm_records.records_service.review
review = review_service.create(
    identity,
    data={
        "type": "community-submission",
        "receiver": {"community": "<community-id>"},
    },
    record=draft._record,  # the underlying record object
)

# 4. Submit for review
#    - If user has "include_directly" permission on community, it auto-accepts
#    - Otherwise, it stays in "submitted" state awaiting curator action
review_service.submit(identity, draft_id)

# --- At this point, the community curator sees the request ---

# 5. Curator accepts (from curator's identity)
from invenio_requests.proxies import current_requests_service
request_id = review.id
current_requests_service.execute_action(
    curator_identity, request_id, "accept", uow=uow
)
# Accepting automatically publishes the record and adds it to the community
```

**Key points:**

- The review request is set on `draft.parent.review` (for first versions)
- Submitting checks `submit_record` permission on the community
- If community review policy is "open", the `include()` method auto-accepts
- Accepting the request triggers record publication automatically

## Workflow 3: Add Published Record to Additional Community

For records that are already published and need to be added to another community.

```python
from invenio_rdm_records.proxies import current_rdm_records

# The record owner initiates inclusion
inclusion_service = current_rdm_records.record_communities_service

# This creates a CommunityInclusion request
result = inclusion_service.add(
    identity,
    record_id,
    data={"communities": [{"id": "<community-id>"}]},
)

# The community curator then accepts via the requests service
# (same as workflow 2 step 5)
```

## Workflow 4: Create a New Version

```python
# 1. Create new version draft from existing record
new_draft = service.new_version(identity, record_id)
new_draft_id = new_draft.id

# 2. Update metadata if needed
service.update_draft(identity, new_draft_id, data={
    "metadata": {
        ...  # updated metadata
    }
})

# 3. Optionally upload new/updated files
# (new version starts with files copied from previous version)

# 4. Publish (or submit for review)
record = service.publish(identity, new_draft_id)
```

## Workflow 5: Edit Published Record Metadata

```python
# 1. Create an edit draft (puts record in "edit mode")
draft = service.edit(identity, record_id)
draft_id = draft.id

# 2. Update the draft
service.update_draft(identity, draft_id, data={
    "metadata": {
        "title": "Updated Title",
        ...  # full metadata required
    }
})

# 3. Re-publish
record = service.publish(identity, draft_id)
```

**Note:** `update_draft` requires the full metadata object — it replaces, not patches.

## Workflow 6: Manage Access (Embargo, Grants, Links)

```python
from invenio_rdm_records.proxies import current_rdm_records

access_service = current_rdm_records.access_service

# Set embargo on a draft
service.update_draft(identity, draft_id, data={
    ...
    "access": {
        "record": "public",
        "files": "restricted",
        "embargo": {
            "active": True,
            "until": "2025-12-31",
            "reason": "Publisher requirement",
        }
    }
})

# Create a secret access link (for sharing restricted records)
link = access_service.create_secret_link(
    identity, record_id,
    data={
        "permission": "view",  # view | preview | edit
        "expires_at": "2025-06-01",
        "description": "For reviewer",
    }
)
print(link.data["token"])  # share this token
```

## Workflow 7: Search Records

```python
# Public search (all published records the identity can see)
results = service.search(identity, params={
    "q": "climate change",
    "sort": "newest",
    "size": 10,
    "page": 1,
})

for hit in results.hits:
    print(hit["metadata"]["title"])

# Search user's own drafts
drafts = service.search_drafts(identity, params={"q": ""})

# Search within a community
from invenio_rdm_records.proxies import current_community_records_service
community_records = current_community_records_service.search(
    identity,
    community_id="<community-id>",
    params={"q": "dataset"},
)
```

## Error Handling

Services raise domain exceptions — catch them appropriately:

```python
from invenio_rdm_records.services.errors import (
    ReviewExistsError,
    ReviewNotFoundError,
    ReviewStateError,
    CommunityRequiredError,
)
from invenio_records_resources.services.errors import PermissionDeniedError

try:
    service.publish(identity, draft_id)
except CommunityRequiredError:
    # Record needs community when RDM_COMMUNITY_REQUIRED_TO_PUBLISH=True
    pass
except PermissionDeniedError:
    # User lacks publish permission
    pass
```

## Using Unit of Work Across Multiple Operations

```python
from invenio_records_resources.services.uow import UnitOfWork

# Group operations into a single transaction
with UnitOfWork() as uow:
    draft = service.create(identity, data={...}, uow=uow)
    service.draft_files.init_files(identity, draft.id, data=[...], uow=uow)
    # ... more operations ...
    uow.commit()  # single DB commit, then indexing
```
