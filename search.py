import math
import json
import os
import sys

from dotenv import load_dotenv
import requests
import requests_ratelimiter
import slugify
import tqdm

MAX_FILES = 1000
PER_PAGE = 100

# Get the JSON Schema Store catalog
catalog = requests.get("https://www.schemastore.org/api/json/catalog.json").json()

# Load .env (for GITHUB_TOKEN)
load_dotenv()

headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": "Bearer " + os.environ["GITHUB_TOKEN"],
    "X-GitHub-Api-Version": "2022-11-28",
}


# Initialize a rate-limited session
session = requests.Session()
adapter = requests_ratelimiter.LimiterAdapter(per_minute=5)
session.mount("http://", adapter)
session.mount("https://", adapter)

schemas = [s for s in catalog["schemas"] if len(s.get("fileMatch", [])) > 0]

for schema in tqdm.tqdm(schemas, position=0):
    output_filename = os.path.join("files", slugify.slugify(schema["name"]) + ".txt")

    # Skip if the output already exists
    if os.path.exists(output_filename):
        continue

    total_results = None
    total_found = 0

    # Start a progress bar with the estimated total
    pbar = tqdm.tqdm(
        total=total_results, position=1, leave=False, postfix={"schema": schema["name"]}
    )

    for filename in schema["fileMatch"]:
        # Strip the leading "**/" if it exists
        filename = filename.removeprefix("**/")
        page = 1
        file_results = MAX_FILES

        # Loop while we still have more pages
        while total_found < MAX_FILES and page <= math.ceil(file_results / PER_PAGE):
            params = {"q": filename + " in:path", "per_page": PER_PAGE, "page": page}
            r = session.get(
                "https://api.github.com/search/code", params=params, headers=headers
            )

            # Break if we get an error
            if r.status_code != requests.codes.ok:
                sys.stderr.write("Error " + str(r.status_code) + "\n")
                sys.stderr.write(json.dumps(r.json()))
                sys.exit(1)

            rj = r.json()

            # Update the total number of results
            file_results = rj["total_count"]
            if not total_results:
                total_results = rj["total_count"]
            else:
                total_results = min(MAX_FILES, total_results + rj["total_count"])
            pbar.total = total_results
            pbar.refresh()

            # Write each URL to file
            with open(output_filename, "a") as f:
                for item in rj["items"]:
                    url = (
                        item["html_url"]
                        .replace("//github.com/", "//raw.githubusercontent.com/")
                        .replace("/blob/", "/")
                    )
                    f.write(url + "\n")
                    pbar.update()
                    total_found += 1

            # Move to the next page
            page += 1

    pbar.close()
