"""A script to import Imperial data into the Invenio awards vocabulary."""

import sys
from pathlib import Path

from ic_data_repo.vocabs import import_imperial_awards_to_invenio

if __name__ == "__main__":
    filename = Path(sys.argv[1])
    import_imperial_awards_to_invenio(filename)
