#!/usr/bin/env bash

# Activate the virtual environment
source /opt/invenio/src/.venv/bin/activate

# Start the application
exec "$@"
