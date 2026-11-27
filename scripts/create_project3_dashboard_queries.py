import json
import sys
from pathlib import Path
from urllib.parse import quote

import requests
from requests.auth import HTTPBasicAuth

ROOT = Path.cwd()
ENV_FILE = ROOT / "config/.env"
CONFIG_FILE = ROOT / "config/project_config.json"
API = "7.1"

def load_env(path):
    values = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values

env = load_env(ENV_FILE)
cfg = json.loads(CONFIG_FILE.read_text())

raw_org = env.get("AZDO_ORG", "").strip().rstrip("/")
ORG = raw_org if raw_org.startswith("https://") else f"https://dev.azure.com/{raw_org}"

PROJECT = env.get("AZDO_PROJECT", cfg["project_name"]).strip()
PAT = env.get("AZDO_PAT", "").strip()

if not ORG or not PROJECT or not PAT:
    sys.exit("Missing Azure DevOps configuration.")

BASE = f"{ORG}/{quote(PROJECT, safe='')}/_apis/wit/queries"

session = requests.Session()
session.auth = HTTPBasicAuth("", PAT)
session.headers.update({"Accept": "application/json"})

def check(response, action):
    if not response.ok:
        raise RuntimeError(
            f"{action}: HTTP {response.status_code}\n{response.text[:2000]}"
        )
    return response.json() if response.content else {}

def walk(node):
    if isinstance(node, list):
        for item in node:
            yield from walk(item)
    elif isinstance(node, dict):
        yield node
        for key in ("children", "value"):
            if key in node:
                yield from walk(node[key])

def get_tree():
    return check(
        session.get(
            BASE,
            params={"$depth": 2, "api-version": API},
            timeout=30
        ),
        "Retrieve query hierarchy"
    )

def find_shared(tree):
    for node in walk(tree):
        if (
            node.get("isFolder")
            and node.get("name", "").strip().lower() == "shared queries"
        ):
            return node
    return None

def get_shared_folder():
    tree = get_tree()
    shared = find_shared(tree)

    if not shared:
        print("Query hierarchy response structure:")
        print(json.dumps(tree, indent=2)[:6000])
        sys.exit(
            "Shared Queries was not found in the API response. "
            "No queries were created."
        )

    return shared

print(f"Organization: {ORG}")
print(f"Project: {PROJECT}")

shared = get_shared_folder()
folder_id = shared["id"]

print(f"Shared Queries folder found: {folder_id}")

queries = {
    "Project3 - Active Work Items":
        "[System.Tags] CONTAINS 'Project3' AND [System.State] = 'Active'",

    "Project3 - New Work Items":
        "[System.Tags] CONTAINS 'Project3' AND [System.State] = 'New'",

    "Project3 - Closed Work Items":
        "[System.Tags] CONTAINS 'Project3' AND [System.State] = 'Closed'",

    "Project3 - Features":
        "[System.Tags] CONTAINS 'Project3' AND [System.WorkItemType] = 'Feature'",

    "Project3 - Epics":
        "[System.Tags] CONTAINS 'Project3' AND [System.WorkItemType] = 'Epic'",
}

existing = {
    child.get("name")
    for child in shared.get("children", [])
}

created = []
skipped = []

for name, condition in queries.items():

    if name in existing:
        print(f"EXISTS: {name}")
        skipped.append(name)
        continue

    wiql = (
        "SELECT [System.Id], [System.WorkItemType], "
        "[System.Title], [System.State] "
        "FROM WorkItems WHERE "
        f"{condition} ORDER BY [System.ChangedDate] DESC"
    )

    payload = {
        "name": name,
        "wiql": wiql
    }

    response = session.post(
        f"{BASE}/{quote(folder_id, safe='')}",
        params={"api-version": API},
        json=payload,
        timeout=30
    )

    result = check(response, f"Create {name}")

    print(f"CREATED: {name} | ID: {result.get('id')}")
    created.append(name)

# Verify by retrieving the hierarchy again.
shared = get_shared_folder()

final_names = {
    child.get("name")
    for child in shared.get("children", [])
}

missing = [name for name in queries if name not in final_names]

print("\n========== PROJECT 3 QUERY RESULTS ==========")
print(f"Created: {len(created)}")
print(f"Already existed: {len(skipped)}")
print(f"Verified: {len(queries) - len(missing)}/{len(queries)}")

if missing:
    print("Missing:", ", ".join(missing))
    sys.exit(2)

print("\nSUCCESS: All five Project 3 dashboard queries verified.")
