# Test Data Sets

This directory contains some infrastructure to populate some realistic test data into
the repository. In brief, this directory contains:

- `dois` - a file containing the dois of the test datasets
- `download_test_data.py` - a script to download the datasets and metadata
- `create_test_data_records.py` - a script to upload the datasets to the running
  repository.

See the individual script for details but the intended usage is, working in the
`test_data` directory, to:

- run `pipenv run python download_test_data.py` as a one-off or in the event of a change
  in `dois`.
- make sure the services have been setup and are running.
- run `pipenv run python create_test_data_records.py`.
