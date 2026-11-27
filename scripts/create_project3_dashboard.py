import os
import json
import base64
import urllib.request
import urllib.error
from pathlib import Path

# Strict Project 3 configuration
PROJECT = "Kubernetes-Platform-Engineering"
TEAM_ID = "81f28f78-bdf4-496c-acae-b786bb17a5b8"
DASHBOARD_NAME = "Project 3 - Kubernetes Platform"

QUERIES = [
    {
        "name": "Active Work Items",
        "id": "6818cc05-7889-4d8f-a63a-e31782b56ee6",
        "type": "tile"
    },
    {
        "name": "New Work Items",
        "id": "ae7e5410-da73-468e-aeea-34007d7a6c35",
        "type": "tile"
    },
    {
        "name": "Closed Work Items",
        "id": "9dd250f7-d1c4-4def-9cb3-7df03fee1202",
        "type": "tile"
    },
    {
        "name": "Features",
        "id": "4bc55a23-0e25-4529-87b9-da2ea251864f",
        "type": "results"
    },
    {
        "name": "Epics",
        "id": "11229d7a-e67a-42d6-818a-e00a5172eac8",
        "type": "results"
    }
]

# Load existing credentials
for line in Path("config/.env").read_text().splitlines():
    if "=" in line and not line.lstrip().startswith("#"):
        key, value = line.split("=", 1)
        os.environ[key.strip()] = value.strip().strip('"').strip("'")

org = os.environ["AZDO_ORG"].strip().rstrip("/")
if not org.startswith("https://"):
    org = f"https://dev.azure.com/{org}"

pat = os.environ["AZDO_PAT"].strip()
auth = base64.b64encode(f":{pat}".encode()).decode()

base = f"{org}/{PROJECT}"
api = "7.1-preview.2"

def request(method, url, payload=None):
    headers = {
        "Authorization": f"Basic {auth}",
        "Accept": "application/json"
    }

    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode()

    req = urllib.request.Request(
        url, data=data, headers=headers, method=method
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as error:
        print(f"\nERROR: HTTP {error.code}")
        print(error.read().decode(errors="replace")[:3000])
        raise

print("=" * 60)
print("PROJECT 3 DASHBOARD CREATION")
print("=" * 60)
print("Project:", PROJECT)
print("Dashboard:", DASHBOARD_NAME)

# Confirm project identity before any write
project_data = request(
    "GET",
    f"{org}/_apis/projects/{PROJECT}?api-version=7.1"
)

if project_data.get("name") != PROJECT:
    raise RuntimeError("Project identity verification failed.")

# Find existing dashboard with the intended name
# Dashboard listing uses the project-level endpoint.
dashboard_list_url = (
    f"{base}/_apis/dashboard/dashboards"
    "?api-version=7.1-preview.3"
)

# Dashboard creation uses the team-scoped endpoint.
dashboards_url = (
    f"{base}/{TEAM_ID}/_apis/dashboard/dashboards"
    f"?api-version={api}"
)

dashboards = request("GET", dashboard_list_url)

existing = next(
    (
        d for d in dashboards.get("value", [])
        if d.get("name") == DASHBOARD_NAME
    ),
    None
)

if existing:
    dashboard_id = existing["id"]
    print("\nResuming existing dashboard:", dashboard_id)
else:
    dashboard = request(
        "POST",
        dashboards_url,
        {
            "name": DASHBOARD_NAME,
            "dashboardScope": "project_Team"
        }
    )
    dashboard_id = dashboard["id"]
    print("\nCreated dashboard:", dashboard_id)

widgets_url = (
    f"{base}/{TEAM_ID}/_apis/dashboard/dashboards/"
    f"{dashboard_id}/widgets?api-version={api}"
)

widget_types = {
    "tile": (
        "ms.vss-dashboards-web."
        "Microsoft.VisualStudioOnline.Dashboards.QueryScalarWidget"
    ),
    "results": (
        "ms.vss-mywork-web."
        "Microsoft.VisualStudioOnline.MyWork.WitViewWidget"
    )
}

created = []

for index, query in enumerate(QUERIES):
    settings = {
        "queryId": query["id"],
        "queryName": query["name"]
    }

    # Query settings are serialized as a JSON string.
    payload = {
        "name": query["name"],
        "position": {
            "row": 1 if index < 3 else (2 if index == 3 else 4),
            "column": index + 1 if index < 3 else 1
        },
        "size": {
            "rowSpan": 2 if query["type"] == "results" else 1,
            "columnSpan": 2 if query["type"] == "results" else 1
        },
        "settings": json.dumps(settings),
        "settingsVersion": {
            "major": 1,
            "minor": 0,
            "patch": 0
        },
        "contributionId": widget_types[query["type"]]
    }

    result = request("POST", widgets_url, payload)
    created.append(result)

    print(
        f"Created: {query['name']} "
        f"| Widget ID: {result.get('id')}"
    )

# Verify dashboard widgets
verified = request("GET", widgets_url)
widget_list = verified.get("value", [])

print("\n" + "=" * 60)
print("DASHBOARD CREATION SUMMARY")
print("=" * 60)
print("Dashboard:", DASHBOARD_NAME)
print("Dashboard ID:", dashboard_id)
print("Widgets verified:", len(widget_list))

for widget in widget_list:
    print("-", widget.get("name"))

print("\nDashboard URL:")
print(
    f"{org}/{PROJECT}/_dashboards/dashboard/"
    f"{dashboard_id}"
)
print("\nProject 3 dashboard creation completed.")
