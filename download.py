import datetime
import glob
import json
import os
import sys
import time

import json5
import jsonschema
import requests
import requests_ratelimiter
import slugify
import toml
import tqdm
import yaml


# Make datetime objects serializable
# This is important since some data files are actually
# YAML which has a native date type unlike JSON
# See https://stackoverflow.com/a/22238613/123695
def json_serial(obj):
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise TypeError("Object of type %s is not JSON serializable" % type(obj))


# Get the JSON Schema Store catalog
catalog = requests.get("https://www.schemastore.org/api/json/catalog.json").json()

schema_names = {slugify.slugify(s["name"]): s["name"] for s in catalog["schemas"]}
schema_urls = {slugify.slugify(s["name"]): s["url"] for s in catalog["schemas"]}

# Initialize a rate-limited session
session = requests.Session()
adapter = requests_ratelimiter.LimiterAdapter(per_second=1)
session.mount("http://", adapter)
session.mount("https://", adapter)

for file in tqdm.tqdm(glob.glob("files/*.txt"), position=0):
    schema_slug = os.path.basename(file).removesuffix(".txt")

    # Try to download and parse the schema
    r = session.get(schema_urls[schema_slug])
    try:
        schema = json5.loads(r.text)
    except (RecursionError, ValueError):
        sys.stderr.write("Schema for " + schema_names[schema_slug] + " invalid.\n")
        continue

    # Skip if the output already exists
    outfile = "jsons/" + schema_slug + ".json"
    if os.path.exists(outfile):
        continue

    with open(file, "r") as f, open(outfile, "w") as out:
        for line in tqdm.tqdm(
            f.readlines(),
            position=1,
            leave=False,
            postfix={"schema": schema_names[schema_slug]},
        ):
            # Download the document
            doc = session.get(line.strip()).text

            # Try loading the document using JSON5, YAML, and TOML
            doc_obj = None
            for load_fn in [json5.loads, yaml.safe_load, toml.loads]:
                try:
                    doc_obj = load_fn(doc)
                    break
                except (ValueError, RecursionError, yaml.YAMLError, toml.decoder.TomlDecodeError):
                    continue

            # If we didn't get a valid dictionary, then stop
            if not doc_obj:
                continue

            # Validate the document and skip if invalid
            try:
                jsonschema.validate(instance=doc_obj, schema=schema)
            except (jsonschema.exceptions.ValidationError, jsonschema.exceptions.SchemaError, RecursionError, TypeError):
                continue

            json.dump(doc_obj, out, default=json_serial)
            out.write("\n")
