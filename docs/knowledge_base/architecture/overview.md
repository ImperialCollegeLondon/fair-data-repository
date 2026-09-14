# Architecture Overview

> InvenioRDM uses a strict three-layer architecture: Presentation → Service → Data
> Access.

**Prerequisites:** None (start here) **Related:** [Service Layer](service-layer.md),
[Data Access Layer](data-access-layer.md), [Presentation Layer](presentation-layer.md)

## The Three Layers

```
┌─────────────────────────────────────────────────┐
│  Presentation Layer                             │
│  (REST Resources, Flask Views, Celery Tasks)    │
│  Parses requests, serializes responses          │
├─────────────────────────────────────────────────┤
│  Service Layer                                  │
│  (Services, Components, Permissions, Schemas)   │
│  Business logic, authorization, validation      │
├─────────────────────────────────────────────────┤
│  Data Access Layer                              │
│  (Record APIs, System Fields, Models, Dumpers)  │
│  Data integrity, storage, indexing              │
└─────────────────────────────────────────────────┘
```

## Data Flow

- **Presentation → Service:** Communicates via "record projections" (a view of a record
    localised to a specific identity/user).
- **Service → Data Access:** Communicates via "record entities" that provide data
    abstraction, syntactic validation, and a programmatic API.

The service layer is **interface-independent** — it knows nothing about HTTP. It can be
called from REST APIs, CLI commands, or Celery tasks identically.

## Key Design Principles

1. **One data representation** — The service layer works with a single representation
    regardless of whether data came from DB or search index.
1. **One primary storage, many secondary** — PostgreSQL is the source of truth;
    OpenSearch holds denormalised copies for fast reads.
1. **Idempotent dumping/loading** — `record == Record.load(record.dump())` always.
1. **Denormalization over normalization** — Read speed preferred over write speed.
1. **Data versioning** — Optimistic concurrency control via version counters.

## Where Does My Code Belong?

Always ask: is this presentation, service, or data access?

| If your code...                               | It belongs in...           |
| --------------------------------------------- | -------------------------- |
| Parses HTTP params, serializes JSON responses | Presentation               |
| Checks permissions, validates business rules  | Service                    |
| Reads/writes to DB or search index            | Data Access                |
| Defines how a record property behaves         | Data Access (system field) |
| Converts between formats for the user         | Presentation (serializer)  |

## Module Layout Convention

A typical InvenioRDM module follows this structure:

```
my_module/
├── records/          # Data access layer
│   ├── api.py        # Record API class
│   ├── models.py     # SQLAlchemy models
│   ├── systemfields/ # System field definitions
│   ├── jsonschemas/  # Structural JSON schemas
│   ├── mappings/     # OpenSearch mappings
│   └── dumpers/      # Dump/load for secondary storage
├── services/         # Service layer
│   ├── service.py    # Service class
│   ├── config.py     # ServiceConfig (dependency injection)
│   ├── schema.py     # Marshmallow schemas (validation)
│   ├── permissions.py
│   └── components/   # Service components
├── resources/        # Presentation layer
│   ├── resource.py   # REST API resource
│   └── config.py     # ResourceConfig
├── views.py          # Flask UI views
└── ext.py            # Flask extension (wires everything together)
```

## Performance Model

- **Reads:** Served primarily from OpenSearch (fast, possibly slightly stale).
- **Writes:** Go to PostgreSQL first, then async-indexed to OpenSearch.
- **DB queries:** Almost exclusively primary key lookups — complex queries go to the
    search index.
- **Immediate consistency:** Critical UX paths (e.g. delete then list) force immediate
    re-indexing.
