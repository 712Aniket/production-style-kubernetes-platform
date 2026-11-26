import os
import json
import base64
import urllib.request
import urllib.error
import urllib.parse

with open("config/project_config.json") as f:
    config = json.load(f)

pat = os.environ.get("AZDO_PAT")
if not pat:
    raise SystemExit("ERROR: AZDO_PAT missing.")

org = config["organization"]
project = config["project_name"]

auth = base64.b64encode(f":{pat}".encode()).decode()
base = f"https://dev.azure.com/{org}/{urllib.parse.quote(project, safe='')}"

def request_api(url, method="GET", payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json-patch+json"
        }
    )
    with urllib.request.urlopen(req) as response:
        return json.load(response)

created_id = None

try:
    create_url = (
        f"{base}/_apis/wit/workitems/$Task?api-version=7.1"
    )

    payload = [
        {
            "op": "add",
            "path": "/fields/System.Title",
            "value": "TEMPORARY - PAT Permission Test - DELETE"
        }
    ]

    result = request_api(create_url, "PATCH", payload)
    created_id = result["id"]

    print("WORK ITEM CREATE: PASS")
    print("Temporary item ID:", created_id)

    delete_url = (
        f"{base}/_apis/wit/workitems/{created_id}?api-version=7.1"
    )

    request_api(delete_url, "DELETE")
    print("WORK ITEM DELETE: PASS")
    print("CLEANUP: SUCCESS")

except urllib.error.HTTPError as error:
    print("HTTP ERROR:", error.code)
    print(error.read().decode()[:1200])

    if created_id:
        print("WARNING: Temporary item may still exist:", created_id)

except Exception as error:
    print("ERROR:", str(error))
    if created_id:
        print("WARNING: Check temporary item:", created_id)
