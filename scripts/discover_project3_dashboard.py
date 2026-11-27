import json
import sys
from pathlib import Path
from urllib.parse import quote

import requests
from requests.auth import HTTPBasicAuth

ROOT = Path.cwd()

def load_env(path):
    values = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            values[k.strip()] = v.strip().strip('"').strip("'")
    return values

env = load_env(ROOT / "config/.env")
cfg = json.loads((ROOT / "config/project_config.json").read_text())

raw_org = env["AZDO_ORG"].strip().rstrip("/")
ORG = raw_org if raw_org.startswith("https://") else f"https://dev.azure.com/{raw_org}"

PROJECT = env.get("AZDO_PROJECT", cfg["project_name"])
PAT = env["AZDO_PAT"]

session = requests.Session()
session.auth = HTTPBasicAuth("", PAT)
session.headers.update({"Accept": "application/json"})

project = quote(PROJECT, safe="")
base = f"{ORG}/{project}/_apis"

def get(url, params, label):
    r = session.get(url, params=params, timeout=30)
    if not r.ok:
        print(f"\n{label}: HTTP {r.status_code}")
        print(r.text[:2000])
        sys.exit(1)
    return r.json()

print("===== PROJECT 3 DASHBOARD DISCOVERY =====")
print("Organization:", ORG)
print("Project:", PROJECT)

# Discover project teams.
teams = get(
    f"{ORG}/_apis/projects/{project}/teams",
    {"api-version": "7.1"},
    "Teams"
)

print("\n===== TEAMS =====")
for team in teams.get("value", []):
    print(json.dumps({
        "name": team.get("name"),
        "id": team.get("id")
    }))

# Discover available dashboard widgets.
widgets = get(
    f"{ORG}/{project}/_apis/dashboard/widgettypes",
    {"$scope": "project_Team", "api-version": "7.1-preview.1"},
    "Widget types"
)

print("\n===== RELEVANT WIDGET TYPES =====")

items = widgets if isinstance(widgets, list) else widgets.get("value", [])

keywords = ("query", "chart", "work", "sprint", "markdown")

for widget in items:
    text = json.dumps(widget).lower()
    if any(keyword in text for keyword in keywords):
        print(json.dumps(widget, indent=2))

# Check existing dashboards for the team.
print("\n===== EXISTING DASHBOARDS =====")

for team in teams.get("value", []):
    team_name = team["name"]
    url = f"{ORG}/{project}/{quote(team_name, safe='')}/_apis/dashboard/dashboards"

    dashboards = get(
        url,
        {"api-version": "7.1-preview.3"},
        "Dashboards"
    )

    for dashboard in dashboards.get("value", []):
        print(json.dumps({
            "team": team_name,
            "name": dashboard.get("name"),
            "id": dashboard.get("id")
        }))

print("\n===== DISCOVERY COMPLETE =====")
