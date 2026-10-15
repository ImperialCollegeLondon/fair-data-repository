# Permissions

> InvenioRDM uses declarative permission policies with "need generators" that produce
> Flask-Principal needs. Policies are highly configurable via config variables.

**Prerequisites:** [Service Layer](../architecture/service-layer.md) **Related:**
[Services Catalogue](../architecture/services-catalogue.md),
[Architecture Overview](../architecture/overview.md)

## How Permissions Work

1. A service method calls
    `self.require_permission(identity, "action_name", record=record)`
1. This looks up `can_<action_name>` on the configured permission policy
1. Each entry in that list is a **need generator** — it produces Flask-Principal `Need`
    objects
1. If the identity provides **any** of the generated needs, access is granted
1. `superuser-access` is always implicitly added (admins always pass)

## Permission Policy Structure

```python
from invenio_records_permissions.policies.records import RecordPermissionPolicy
from invenio_records_permissions.generators import AnyUser, SystemProcess

class MyPermissionPolicy(RecordPermissionPolicy):
    # High-level composable permissions
    can_manage = [RecordOwners(), SystemProcess()]
    can_curate = SameAs("can_manage") + [AccessGrant("edit")]

    # Action permissions
    can_create = [AuthenticatedUser(), SystemProcess()]
    can_read = [IfRestricted("record", then_=SameAs("can_view"), else_=SameAs("can_all"))]
    can_update_draft = SameAs("can_review")
    can_publish = SameAs("can_review")
    can_delete = [Administration(), SystemProcess()]
```

**Key patterns:**

- `SameAs("can_x")` — reuses another permission list (composability)
- `SameAs("can_x") + [Extra()]` — extends another permission list
- Conditional generators (`IfRestricted`, `IfConfig`, `IfNewRecord`) — branching logic

## Built-in Need Generators

### Basic Generators (`invenio_records_permissions.generators`)

| Generator                               | Grants to                                    |
| --------------------------------------- | -------------------------------------------- |
| `AnyUser()`                             | Everyone (including anonymous)               |
| `AuthenticatedUser()`                   | Any logged-in user                           |
| `SystemProcess()`                       | System identity only (background tasks, CLI) |
| `Disable()`                             | Nobody (explicitly disables an action)       |
| `SameAs("can_x")`                       | Same needs as another permission attribute   |
| `IfConfig("VAR", then_=..., else_=...)` | Conditional on app config                    |

### RDM-Specific Generators (`invenio_rdm_records.services.generators`)

| Generator                         | Grants to                                                  |
| --------------------------------- | ---------------------------------------------------------- |
| `RecordOwners()`                  | The user who owns the record (`parent.access.owned_by`)    |
| `AccessGrant(permission)`         | Users/roles with a specific access grant level             |
| `SecretLinks(permission)`         | Holders of a secret link with sufficient permission        |
| `SubmissionReviewer()`            | Community reviewers for the submission request             |
| `RequestReviewers()`              | Reviewers assigned to a request                            |
| `RecordCommunitiesAction(action)` | Community members with a given role action (e.g. "curate") |
| `CommunityInclusionReviewers()`   | Members reviewing community inclusion requests             |
| `ResourceAccessToken(access)`     | Holders of a resource access token                         |

### Conditional Generators

| Generator                               | Condition                                       |
| --------------------------------------- | ----------------------------------------------- |
| `IfRestricted(field, then_, else_)`     | Record/files access is "restricted" vs "public" |
| `IfNewRecord(then_, else_)`             | No record exists yet (creation context)         |
| `IfDeleted(then_, else_)`               | Record has been soft-deleted                    |
| `IfRecordDeleted(then_, else_)`         | Like IfDeleted but with query filter support    |
| `IfDraft(then_, else_)`                 | Record is a draft                               |
| `IfExternalDOIRecord(then_, else_)`     | Record has an externally-provided DOI           |
| `IfCreate(then_, else_)`                | Request is being created (not modified)         |
| `IfRequestType(type_cls, then_, else_)` | Request is of a specific type                   |
| `IfConfig(var, then_, else_)`           | Flask config variable is truthy                 |
| `IfOneCommunity(then_, else_)`          | Record belongs to exactly one community         |
| `IfAtLeastOneCommunity(then_, else_)`   | Record belongs to one or more communities       |

## Configuration Variables That Affect Permissions

These `invenio.cfg` settings alter permission behaviour via `IfConfig`:

| Config Variable                                 | Default | Effect                                                                                         |
| ----------------------------------------------- | ------- | ---------------------------------------------------------------------------------------------- |
| `RDM_ALLOW_METADATA_ONLY_RECORDS`               | `True`  | When True, users can toggle file uploads off. When False, only SystemProcess can.              |
| `RDM_ALLOW_RESTRICTED_RECORDS`                  | `True`  | When True, users can set access restrictions. When False, feature is disabled.                 |
| `RDM_COMMUNITY_REQUIRED_TO_PUBLISH`             | `False` | When True, records must belong to a community to be published (only Admin/System can bypass).  |
| `RDM_ALLOW_EXTERNAL_DOI_VERSIONING`             | `True`  | When True, external DOI records can be versioned normally. When False, only SystemProcess can. |
| `RDM_ALLOW_OWNERS_REMOVE_COMMUNITY_FROM_RECORD` | `True`  | When True, record owners can remove their record from a community.                             |

## Permission Hierarchy (Default Policy)

The default `RDMRecordPermissionPolicy` builds a hierarchy:

```
can_manage     (owner, community curators with "curate" action, manage-grant, system)
  └── can_curate   = can_manage + edit-grant + edit-links
       └── can_review  = can_curate + submission reviewer
            └── can_preview = can_review + preview-grant + preview-links + request reviewers
                 └── can_view    = can_preview + view-grant + view-links + inclusion reviewers
```

Actions reference these levels:

- `can_create` → `AuthenticatedUser`
- `can_read` → if restricted: `can_view`; if public: `AnyUser`
- `can_update_draft` → `can_review`
- `can_publish` → `can_review` (or requires community if configured)
- `can_edit` → `can_curate` (unless deleted)
- `can_delete` → `Administration` + `SystemProcess`

## Customising Permissions

### Override the entire policy

```python
# invenio.cfg
from my_site.permissions import MyPermissionPolicy
RDM_PERMISSION_POLICY = MyPermissionPolicy
```

### Extend the default policy

```python
from invenio_rdm_records.services.permissions import RDMRecordPermissionPolicy
from invenio_records_permissions.generators import SystemProcess
from my_site.generators import MyCustomGenerator

class MyPermissionPolicy(RDMRecordPermissionPolicy):
    can_create = [MyCustomGenerator(), SystemProcess()]
```

### Write a custom generator

```python
from invenio_records_permissions.generators import Generator
from flask_principal import ActionNeed

class AbleToDeposit(Generator):
    def needs(self, **kwargs):
        return [ActionNeed("deposit-action")]
```

The identity must provide the need (typically assigned at login via a signal handler or
role assignment).

## Checking Permissions Imperatively (in Components or Services)

Use `self.service.require_permission(identity, "action_name")` — not a `Permission`
object directly. There are two `Permission` classes in the dependency tree and they
behave very differently:

| Class                                                      | How it checks                                                                                     | Works in components?                           |
| ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| `flask_principal.Permission`                               | Checks `identity.provides` directly — `ActionNeed` objects are **never** in that set at runtime   | ❌ Always denies                               |
| `invenio_access.permissions.Permission`                    | Queries `ActionUsers` DB table to expand `ActionNeed → UserNeed`, then checks `identity.provides` | ✅ But requires app context and is lower-level |
| `self.service.require_permission(identity, "action_name")` | Uses the configured `permission_policy_cls`; raises `PermissionDeniedError` on failure            | ✅ Canonical pattern                           |

The resource layer registers an error handler for
`invenio_records_resources.services.errors.PermissionDeniedError` (HTTP 403). It does
**not** catch bare `flask_principal.PermissionDenied`, so never raise that directly.

```python
# ✅ Correct — raises PermissionDeniedError caught as HTTP 403
self.service.require_permission(identity, "use_subject_field")

# ❌ Wrong — flask_principal.Permission never matches ActionNeed in identity
from flask_principal import Permission, ActionNeed
if not Permission(ActionNeed("subject-action")).allows(identity):
    raise PermissionDenied()
```

To expose a new permission action in the policy, add a `can_<action>` list and a
matching generator:

```python
from invenio_access.permissions import ActionUsers
from invenio_rdm_records.services.permissions import RDMRecordPermissionPolicy
from invenio_records_permissions.generators import Generator, SystemProcess
from flask_principal import ActionNeed

subject_metadata_action = ActionNeed("subject-metadata-action")

class AbleToUseSubjectField(Generator):
    def needs(self, **kwargs):
        return [subject_metadata_action]

    def query_filter(self, **kwargs):
        return []  # not used for search filtering

class MyPermissionPolicy(RDMRecordPermissionPolicy):
    can_use_subject_field = [AbleToUseSubjectField(), SystemProcess()]
```

Grant the action to a user via the database (in tests or admin CLI):

```python
from invenio_access.permissions import ActionUsers
db.session.add(ActionUsers.allow(subject_metadata_action, user_id=user.id))
db.session.commit()
```

## Query Filters

Generators also define `query_filter()` methods used for search-time filtering. This
ensures users only see records they have permission to access in search results. For
example, `RecordOwners.query_filter()` adds an OpenSearch term filter on
`parent.access.owned_by.user`.
