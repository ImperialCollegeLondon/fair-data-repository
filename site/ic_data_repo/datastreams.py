"""Datastreams for vocabulary entries."""

import yaml
from invenio_vocabularies.datastreams.readers import BaseReader
from invenio_vocabularies.datastreams.writers import ServiceWriter


class AffiliationsWriter(ServiceWriter):
    """A writer for vocabulary entries to the affiliations service."""

    def __init__(self, *args, **kwargs):
        """Constructor."""
        service_or_name = kwargs.pop("service_or_name", "affiliations")
        super().__init__(service_or_name=service_or_name, *args, **kwargs)

    def _entry_id(self, entry):
        """Get the id from an entry."""
        return entry["id"]


class StreamingYamlSequenceReader(BaseReader):
    """A reader for YAML sequences that streams the data as it is read.

    Streams the first sequence found in the first document only of a YAML file.
    """

    def _iter(self, fp, *args, **kwargs):
        loader = yaml.SafeLoader(fp)

        # consume file until we hit the first sequence
        while not isinstance(loader.get_event(), yaml.events.SequenceStartEvent):
            pass

        # recursively load individual items until we get to the end of the sequenc
        while not isinstance(loader.peek_event(), yaml.events.SequenceEndEvent):
            loader.constructed_objects = {}  # stop memory accumulation in loader cache
            yield loader.construct_object(loader.compose_node(None, None), deep=True)
