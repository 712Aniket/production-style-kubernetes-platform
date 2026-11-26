import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "config/work_item_catalog.json"
OUTPUT = ROOT / "exports/project3_azure_boards_import.csv"

with SOURCE.open(encoding="utf-8") as f:
    data = json.load(f)

items = data["items"]
expected = {"Epic": 12, "Feature": 40, "User Story": 80, "Task": 160}
actual = Counter(item["type"] for item in items)

if dict(actual) != expected:
    raise SystemExit(f"Count mismatch: {dict(actual)}")

by_title = defaultdict(list)
for item in items:
    by_title[item["title"]].append(item)

# Resolve every parent reference unambiguously.
children = defaultdict(list)
roots = []

for item in items:
    parent = item.get("parent")

    if not parent:
        if item["type"] != "Epic":
            raise SystemExit(f"Unexpected root item: {item['title']}")
        roots.append(item)
        continue

    matches = by_title[parent]
    if len(matches) != 1:
        raise SystemExit(
            f"Parent reference is missing or ambiguous: {parent}"
        )

    children[id(matches[0])].append(item)

# Validate the expected hierarchy.
expected_parent = {
    "Feature": "Epic",
    "User Story": "Feature",
    "Task": "User Story",
}

for item in items:
    if item.get("parent"):
        parent = by_title[item["parent"]][0]
        if expected_parent.get(item["type"]) != parent["type"]:
            raise SystemExit(
                f"Invalid hierarchy: {item['title']} -> {parent['title']}"
            )

# Build Azure Boards' indented tree CSV in parent-first order.
rows = []
visited = set()

def walk(item, level):
    if id(item) in visited:
        raise SystemExit(f"Duplicate/cyclic item: {item['title']}")

    visited.add(id(item))

    row = {
        "Work Item Type": item["type"],
        "Title 1": "",
        "Title 2": "",
        "Title 3": "",
        "Title 4": "",
        "Description": item.get("description", ""),
        "Tags": "; ".join(item.get("tags", [])),
    }
    row[f"Title {level}"] = item["title"]
    rows.append(row)

    for child in children[id(item)]:
        walk(child, level + 1)

for epic in roots:
    walk(epic, 1)

if len(rows) != 292 or len(visited) != len(items):
    raise SystemExit(
        f"Export validation failed: {len(rows)} rows, "
        f"{len(visited)} unique items"
    )

fields = [
    "Work Item Type",
    "Title 1",
    "Title 2",
    "Title 3",
    "Title 4",
    "Description",
    "Tags",
]

with OUTPUT.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

print("EXPORT SUCCESSFUL")
print("File:", OUTPUT)
print("Work items:", len(rows))
print("Types:", dict(actual))
print("Hierarchy: Epic > Feature > User Story > Task")
print("Original catalogue: unchanged")
