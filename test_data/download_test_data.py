"""Script to download realistic test datasets for the Imperial Fair Data Repository.

Should be run from the `test_data` directory. Does the following:

- Opens a file called 'dois' in the working directory that contains a DOI on each line.
- For each doi:
  - Pulls metadata for each DOI from Datacite API.
  - Creates a directory name using the DOI value with all '/' replaced by '_'.
  - Saves the metadata into the DOI directory as `metadata.json`.
  - Downloads and saves data files associated with the DOI into its directory.
"""

import base64
import re
from pathlib import Path

import requests


def get_filename_from_scheme_uri(uri):
    """Get filename from b64 encoded URI."""
    encoded = uri.lstrip("filename://")
    return base64.b64decode(encoded.encode("ascii")).decode("ascii")


FILE_URI_REGEX = re.compile(
    "https://data.hpc.imperial.ac.uk/resolve/\\?doi=\\d+\\&file=\\d+"
)
"""Regex to check if a related identifier refers to a data file."""

DATACITE_API_PATH = "https://api.datacite.org/dois/"
"""Root URL of the Datacite API used to retrieve metadata."""


if __name__ == "__main__":
    with open("dois", "r") as f:
        dois = f.read().strip().split("\n")

    for doi in dois:
        # get data from datacite API
        response = requests.get(DATACITE_API_PATH + doi)
        response.raise_for_status()
        metadata = response.json()

        # create directory and write metadata
        dir_path = Path(doi.replace("/", "_"))
        dir_path.mkdir(exist_ok=True)
        with open(dir_path / "metadata.json", "wb") as f:
            f.write(response.content)

        # download files
        for ri in metadata["data"]["attributes"]["relatedIdentifiers"]:
            if not FILE_URI_REGEX.match(ri["relatedIdentifier"]):
                continue

            response = requests.get(ri["relatedIdentifier"])
            response.raise_for_status()

            with open(
                dir_path / get_filename_from_scheme_uri(ri["schemeUri"]), "wb"
            ) as f:
                f.write(response.content)
