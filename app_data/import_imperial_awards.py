"""A script to import Imperial data into the Invenio awards vocabulary."""

import sys
from pathlib import Path

from ic_data_repo.vocabs import import_imperial_awards_to_invenio

if __name__ == "__main__":
    try:
        filename = Path(sys.argv[1])
    except IndexError:
        print("Usage: python import_imperial_awards.py <filename>")
        sys.exit(1)
    import_imperial_awards_to_invenio(filename)
