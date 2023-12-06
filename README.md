# json-fetcher
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/michaelmior/json-fetcher/main.svg)](https://results.pre-commit.ci/latest/github/michaelmior/json-fetcher/main)

## Setup

Dependencies for this project are managed by [pipenv](https://pipenv.pypa.io/) and can be installed with `pipenv install`.
When fetching from GitHub, an [access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) is required and the `GITHUB_TOKEN` environment variable must be set.
The simplest way to do this is to use a `.env` file in the root of the project.

## Usage

1. Collect a list of of JSON documents using the GitHub search API. URLs to documents are stored in the `files` directory.

   pipenv run python search.py

2. Download and validate the schemas JSON documents using the URLs collected in the first step. Schemas will be written to the `schemas` directory and one JSON document per line will be written to the `jsons` directory.

   pipenv run python download.py
