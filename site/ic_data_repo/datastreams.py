"""Datastream classes for handling vocabulary data."""

from typing import Optional, TextIO

from invenio_vocabularies.datastreams.readers import BaseReader


class FileLikeReader(BaseReader):
    """A datastream reader for reading from file-like objects.

    This reader is intended to be chained in front of other readers that expect to
    open a file. This reader expects a file-like object to be passed as it's origin.
    """

    def _iter(self, fp: TextIO, *args, **kwargs):
        """Simply yields the file-like object for further process by other readers."""
        yield fp

    def read(self, item: Optional[TextIO] = None, *args, **kwargs):
        """Passes through item if provided or reads from origin."""
        if item:
            yield from self._iter(item, *args, **kwargs)
        else:
            yield from self._iter(self._origin, *args, **kwargs)
