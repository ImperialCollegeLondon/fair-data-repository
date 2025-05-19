"""Symplectic service component."""

import pprint

from invenio_records_resources.services.records.components import ServiceComponent

from ..symplectic_interface import SymplecticClient


class SymplecticComponent(ServiceComponent):
    """Component to handle Symplectic API interactions."""

    def publish(self, identity, draft=None, record=None):
        """Publish a record to Symplectic."""
        client = SymplecticClient()
        print("Type of record:", type(record))
        pprint.pprint(record)
        client.create_record(record)
