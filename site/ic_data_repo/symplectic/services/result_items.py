"""Imperial College Data Repository Symplectic Service Result Items."""

from invenio_records_resources.services.base import ServiceItemResult


class SymplecticRelatedObjectsResult(ServiceItemResult):
    """Result item for symplectic related objects."""

    def __init__(self, service, identity, related_publications):
        """Initialize the result item."""
        self._service = service
        self._identity = identity
        self._related_publications = related_publications

    @property
    def data(self):
        """Return the related objects data."""
        return self._related_publications

    def to_dict(self):
        """Return the related objects as a dictionary."""
        return {
            "results": [
                {"id": obj.get("id"), "title": obj.get("title"), "doi": obj.get("doi")}
                for obj in self._related_publications
            ],
            "count": len(self._related_publications),
            "links": {"self": "/api/symplectic/related-objects"},
        }
