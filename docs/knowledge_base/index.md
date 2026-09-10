# InvenioRDM Knowledge Base

## Purpose

This knowledge base documents InvenioRDM architecture, customisation patterns, and
project-specific decisions. It is designed for both human developers and AI agents —
documents are kept small and self-contained so agents can selectively load only what
they need.

It condenses useful information about the InvenioRDM ecosystem rather than covering
features or customisations implemented in Helix.

## How to use (for AI agents)

1. Start here — read only the section relevant to your task.
1. Each document begins with a one-line summary and lists prerequisites.
1. Follow cross-links only when you need deeper context.
1. Documents are ≤ 3KB each to minimise context window usage.

## Contents

### Architecture

Core InvenioRDM architecture — read these first for foundational understanding.

- [Overview](architecture/overview.md) — Three-layer architecture and data flow
- [Data Access Layer](architecture/data-access-layer.md) — Records, system fields,
    dumpers, mappings
- [Service Layer](architecture/service-layer.md) — Services, config, UoW, components,
    permissions
- [Services Catalogue](architecture/services-catalogue.md) — Built-in services, proxies,
    and import patterns
- [Presentation Layer](architecture/presentation-layer.md) — Resources, views, Celery
    tasks
- [Vocabularies](architecture/vocabularies.md) — Controlled terms, fixture lifecycle,
    and live updates

### Customisation

How to extend and customise InvenioRDM.

- [Permissions](customisation/permissions.md) — Permission policies, generators, config
    interaction, and hierarchy
- [Custom Fields](customisation/custom-fields.md) — Adding custom metadata fields, UI
    widgets, and facets
- [Service Workflows](customisation/service-workflows.md) — Step-by-step examples:
    create, publish, review, versioning
- [Extension Wiring](customisation/extension-wiring.md) — ext.py, webpack.py, entry
    points, blueprints
- [Service Components](customisation/service-components.md) — Writing custom service
    components
- [File Transfers](customisation/file-transfers.md) — Pluggable file transfer providers,
    schemas, permissions, and lifecycle
- [Templates and Assets](customisation/templates-and-assets.md) — Jinja2 templates,
    LESS, JS overrides
- [Search and Mappings](customisation/search-and-mappings.md) — OpenSearch mappings and
    custom facets

### Project

Specific to this InvenioRDM instance (Imperial College Data Repository).

- [Overview](project/overview.md) — Instance architecture and key decisions
- [IC Data Repo Extension](project/ic-data-repo-extension.md) — The site/ module
- [Deployment](project/deployment.md) — Docker, CI/CD, environments

### Testing

- [Testing](testing.md) — Test patterns, DB session behaviour, permission grants, token
    creation, publish requirements

## Source

Based on official docs from
[inveniosoftware/docs-invenio-rdm](https://github.com/inveniosoftware/docs-invenio-rdm)
(`docs/maintenance/`) supplemented by source code analysis and project experience.
