import os
import json
import base64
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / "config" / ".env")
CONFIG_PATH = ROOT / "config" / "project_config.json"

if not CONFIG_PATH.exists():
    raise SystemExit("ERROR: project_config.json not found.")

config = json.loads(CONFIG_PATH.read_text())
pat = os.environ.get("AZDO_PAT")

if not pat:
    raise SystemExit("ERROR: AZDO_PAT is missing or not exported.")

org = config["organization"]
project_id = config["project_id"]
team_id = config["team_id"]

auth = base64.b64encode(f":{pat}".encode()).decode()
base = f"https://dev.azure.com/{org}"

def get_api(path):
    url = f"{base}/{path}"
    request = urllib.request.Request(
        url,
        headers={"Authorization": f"Basic {auth}"}
    )
    with urllib.request.urlopen(request) as response:
        return json.load(response)

print("\n=== AZURE DEVOPS VERIFICATION ===")

try:
    project = get_api(
        f"_apis/projects/{project_id}?api-version=7.1"
    )
    print("PROJECT ACCESS: PASS")
    print("Project:", project["name"])

    teams = get_api(
        f"_apis/projects/{project_id}/teams?api-version=7.1"
    )
    matching_team = next(
        (t for t in teams.get("value", []) if t["id"].lower() == team_id.lower()),
        None
    )

    if not matching_team:
        raise RuntimeError("Configured team ID was not found.")

    print("TEAM ACCESS: PASS")
    print("Team:", matching_team["name"])

    work_item_types = get_api(
        f"{urllib.parse.quote(project['name'], safe='')}"
        f"/_apis/wit/workitemtypes?api-version=7.1"
    )

    available_types = {
        item["name"] for item in work_item_types.get("value", [])
    }

    print("\n=== AGILE WORK ITEM TYPES ===")
    for item in sorted(available_types):
        print("-", item)

    required = {"Epic", "Feature", "User Story", "Task"}
    missing = required - available_types

    if missing:
        print("\nMISSING TYPES:", ", ".join(sorted(missing)))
    else:
        print("\nREQUIRED HIERARCHY: PASS")

    print("\nREAD VERIFICATION: SUCCESS")

except urllib.error.HTTPError as error:
    print("\nAPI ERROR:", error.code)
    print(error.read().decode()[:1200])
except Exception as error:
    print("\nVERIFICATION ERROR:", str(error))
