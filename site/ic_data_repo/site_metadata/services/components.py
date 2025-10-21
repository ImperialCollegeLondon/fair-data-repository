"""Site Metadata service components."""

from flask import current_app
from invenio_records_resources.services.records.components import ServiceComponent
from opensearchpy import OpenSearch

from .errors import MetadataFileNotFoundError


class MetadataIndexComponent(ServiceComponent):
    """On publish: read attached metadata file, parse again, index."""

    def publish(self, identity, record=None, **kwargs):
        """Index metadata on publish."""
        service = self.service
        cfg = service.config
        attr = cfg.site_metadata_attr
        mapping = (record or {}).get(attr) or {}
        if not mapping:
            return

        client: OpenSearch = current_app.extensions["invenio-search"].client

        for fmt, entry in mapping.items():
            spec = cfg.supported_formats.get(fmt)
            if not spec:
                continue
            file_key = entry.get("file_key")
            if not file_key:
                continue

            files = getattr(record, "files", None)
            if not files or file_key not in files:
                raise MetadataFileNotFoundError(file_key)

            obj = files.get(file_key).object_version
            raw = obj.file.storage().open().read()

            try:
                parsed = service._validators[fmt](raw)
            except Exception as ex:
                current_app.logger.warning(
                    "Skipping metadata indexing for %s (%s): %s", record.id, fmt, ex
                )
                continue

            doc = {
                "record_id": str(record.id),
                "format": fmt,
                "file_key": file_key,
                "metadata": parsed,  # parsed JSON or JSON-LD dict
            }
            client.index(
                index=spec["index_name"],
                id=f"{record.id}-{fmt}",
                body=doc,
                refresh="false",
            )
