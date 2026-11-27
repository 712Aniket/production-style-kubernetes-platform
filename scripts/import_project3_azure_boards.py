#!/usr/bin/env python3
"""Create Project 3 Azure Boards work items directly through the Azure DevOps REST API.

Run from the Kubernetes-Platform-Engineering repository root.
Uses the same config.py settings as the Project 2 automation:
    AZDO_ORG, AZDO_PROJECT, AZDO_PAT

Default mode is preview only. Use --apply to create missing work items.
Existing exact title/type matches are reused, making reruns safe after partial failures.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path
from urllib.parse import quote

import requests
from requests.auth import HTTPBasicAuth

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / 'config' / '.env')
CATALOG = ROOT / "config" / "work_item_catalog.json"
CONFIG_PATH = ROOT / "config" / "project_config.json"

if not CONFIG_PATH.is_file():
    raise SystemExit(f"Project configuration not found: {CONFIG_PATH}")

PROJECT_CONFIG = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
AZDO_ORG = PROJECT_CONFIG["organization"]
AZDO_PROJECT = PROJECT_CONFIG["project_name"]
AZDO_PAT = __import__("os").environ.get("AZDO_PAT")

if not AZDO_PAT:
    raise SystemExit("AZDO_PAT is missing. Export the Project 3 PAT before running this script.")
if not CATALOG.is_file():
    raise SystemExit(f"Catalogue not found: {CATALOG}")

API_VERSION = "7.1"
BASE = f"https://dev.azure.com/{AZDO_ORG}"
PROJECT = quote(AZDO_PROJECT, safe="")
AUTH = HTTPBasicAuth("", AZDO_PAT)
S = requests.Session()
S.auth = AUTH
S.headers.update({"Accept": "application/json"})


def request(method: str, url: str, **kwargs):
    for attempt in range(5):
        response = S.request(method, url, timeout=60, **kwargs)
        if response.status_code not in (429, 500, 502, 503, 504):
            return response
        time.sleep(min(2 ** attempt, 20))
    return response


def fail(response, action: str):
    raise RuntimeError(
        f"{action} failed: HTTP {response.status_code}\n{response.text[:2000]}"
    )


def load_catalogue():
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    if data.get("project") != AZDO_PROJECT:
        raise SystemExit(
            f"Catalogue project is {data.get('project')!r}, but config.py targets {AZDO_PROJECT!r}."
        )
    items = data.get("items")
    if not isinstance(items, list):
        raise SystemExit("Catalogue must contain an 'items' array.")

    expected = {"Epic": 12, "Feature": 40, "User Story": 84, "Task": 168}
    counts = Counter(x.get("type") for x in items)
    if len(items) != 304 or dict(counts) != expected:
        raise SystemExit(f"Unexpected catalogue counts: {dict(counts)}; expected {expected}.")

    # Validate unique (type,title), parent existence, and parent-first ordering.
    seen = {}
    expected_parent = {
        "Epic": None, "Feature": "Epic",
        "User Story": "Feature", "Task": "User Story"
    }
    for index, item in enumerate(items):
        kind, title = item.get("type"), item.get("title")
        if kind not in expected_parent or not title:
            raise SystemExit(f"Invalid item at catalogue index {index}: {item}")
        key = (kind, title)
        if key in seen:
            raise SystemExit(f"Duplicate catalogue item: {key}")
        parent_title = item.get("parent")
        if expected_parent[kind] is None:
            if parent_title is not None:
                raise SystemExit(f"Epic unexpectedly has a parent: {title}")
        else:
            parent_kind = expected_parent[kind]
            if not parent_title or (parent_kind, parent_title) not in seen:
                raise SystemExit(
                    f"Parent missing or not earlier in catalogue for {kind}: {title} -> {parent_title}"
                )
        seen[key] = item
    return data, items


def get_existing_items():
    wiql = (
        "SELECT [System.Id], [System.WorkItemType], [System.Title] "
        "FROM WorkItems WHERE [System.TeamProject] = @project "
        "AND [System.Tags] CONTAINS 'Project3' "
        "ORDER BY [System.Id]"
    )
    r = request(
        "POST",
        f"{BASE}/{PROJECT}/_apis/wit/wiql",
        params={"api-version": API_VERSION},
        json={"query": wiql},
    )
    if not r.ok:
        fail(r, "Query existing Project3 work items")
    try:
        payload = r.json()
    except ValueError:
        print("\\nAZURE DEVOPS RESPONSE DIAGNOSTICS")
        print("HTTP status:", r.status_code)
        print("Content-Type:", r.headers.get("Content-Type"))
        print("Response body:")
        print(r.text[:2000])
        raise
    refs = payload.get("workItems", [])
    found = {}
    for start in range(0, len(refs), 200):
        ids = ",".join(str(x["id"]) for x in refs[start:start + 200])
        if not ids:
            continue
        r = request(
            "GET", f"{BASE}/{PROJECT}/_apis/wit/workitems",
            params={"ids": ids, "fields": "System.Id,System.WorkItemType,System.Title,System.Tags",
                    "api-version": API_VERSION}
        )
        if not r.ok:
            fail(r, "Read existing Project3 work items")
        for item in r.json().get("value", []):
            f = item["fields"]
            key = (f["System.WorkItemType"], f["System.Title"])
            if key in found:
                raise RuntimeError(f"Multiple existing Project3 items match {key}; refusing to guess.")
            found[key] = item["id"]
    return found


def create_item(item, parent_id=None):
    kind = item["type"]
    fields = [
        {"op": "add", "path": "/fields/System.Title", "value": item["title"]},
        {"op": "add", "path": "/fields/System.Description", "value": item.get("description", "")},
        {"op": "add", "path": "/fields/System.Tags",
         "value": "; ".join(item.get("tags", ["Project3"]))},
    ]
    if item.get("acceptance_criteria"):
        fields.append({
            "op": "add", "path": "/fields/Microsoft.VSTS.Common.AcceptanceCriteria",
            "value": item["acceptance_criteria"]
        })
    if parent_id is not None:
        fields.append({
            "op": "add", "path": "/relations/-",
            "value": {
                "rel": "System.LinkTypes.Hierarchy-Reverse",
                "url": f"{BASE}/_apis/wit/workItems/{parent_id}",
                "attributes": {"comment": "Parent relationship created by Project 3 catalogue automation"}
            }
        })
    r = request(
        "POST",
        f"{BASE}/{PROJECT}/_apis/wit/workitems/${quote(kind, safe='')}",
        params={"api-version": API_VERSION},
        json=fields,
        headers={"Content-Type": "application/json-patch+json"},
    )
    if not r.ok:
        fail(r, f"Create {kind}: {item['title']}")
    return r.json()["id"]


def main():
    parser = argparse.ArgumentParser(description="Create Project 3 Azure Boards hierarchy via REST API.")
    parser.add_argument("--apply", action="store_true", help="create missing work items; default is preview")
    args = parser.parse_args()

    data, items = load_catalogue()
    print(f"Organization : {AZDO_ORG}")
    print(f"Project      : {AZDO_PROJECT}")
    print(f"Catalogue    : {CATALOG}")
    print(f"Hierarchy    : {data.get('hierarchy')}")
    print("Catalogue validation: PASS (12 Epics, 40 Features, 84 User Stories, 168 Tasks = 304)")
    existing = get_existing_items()
    print(f"Existing matching Project3 items: {len(existing)}")

    # Parent-first order is validated in load_catalogue.
    title_to_id = {}
    missing = []
    for item in items:
        key = (item["type"], item["title"])
        if key in existing:
            title_to_id[item["title"]] = existing[key]
            continue
        parent_id = title_to_id.get(item.get("parent")) if item.get("parent") else None
        missing.append((item, parent_id))
        # A planned parent does not have an ID until --apply.
        title_to_id[item["title"]] = None

    counts = Counter(x["type"] for x, _ in missing)
    print("\nItems to create:")
    for kind in ("Epic", "Feature", "User Story", "Task"):
        print(f"  {kind}: {counts[kind]}")
    print(f"  TOTAL: {len(missing)}")

    if not args.apply:
        print("\nPREVIEW ONLY — Azure Boards was not changed.")
        print("After reviewing, run: python scripts/import_project3_azure_boards.py --apply")
        return 0

    # Re-resolve parent IDs while creating, so each child links to the actual parent ID.
    ids_by_title = dict((title, item_id) for (kind, title), item_id in existing.items())
    created = 0
    reused = 0
    for item in items:
        key = (item["type"], item["title"])
        if key in existing:
            reused += 1
            ids_by_title[item["title"]] = existing[key]
            continue
        parent_title = item.get("parent")
        parent_id = ids_by_title.get(parent_title) if parent_title else None
        if parent_title and parent_id is None:
            raise RuntimeError(f"Cannot resolve parent ID for {item['title']}: {parent_title}")
        new_id = create_item(item, parent_id)
        ids_by_title[item["title"]] = new_id
        existing[key] = new_id
        created += 1
        print(f"CREATED #{new_id} [{item['type']}] {item['title']}")

    print(f"\nCreation finished. Created: {created}; reused: {reused}.")
    print("Re-querying Azure Boards to verify saved items...")
    verified = get_existing_items()
    errors = []
    final_counts = Counter()
    for item in items:
        key = (item["type"], item["title"])
        if key not in verified:
            errors.append(f"Missing: {key}")
        else:
            final_counts[item["type"]] += 1
    if errors:
        print("\nVERIFICATION FAILED:")
        for error in errors:
            print("  " + error)
        return 3
    expected = {"Epic": 12, "Feature": 40, "User Story": 84, "Task": 168}
    if dict(final_counts) != expected:
        print(f"Count mismatch: {dict(final_counts)}")
        return 3
    print("VERIFICATION SUCCESSFUL:")
    for kind in ("Epic", "Feature", "User Story", "Task"):
        print(f"  {kind}: {final_counts[kind]}")
    print("  TOTAL: 304")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except requests.RequestException as exc:
        raise SystemExit(f"Network/API request failed: {exc}")
