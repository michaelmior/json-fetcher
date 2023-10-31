# json-fetcher
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/michaelmior/json-fetcher/main.svg)](https://results.pre-commit.ci/latest/github/michaelmior/json-fetcher/main)
1. Collect a list of of JSON documents using the GitHub search API.

   pipenv run python search.py

2. Fetch the JSON documents using the URLs collected in the first step.

   pipenv run python download.py

3. (TODO) Validate the set of collected documents according to the schema.
