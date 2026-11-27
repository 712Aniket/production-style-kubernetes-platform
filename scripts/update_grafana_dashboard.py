import json
import os
import subprocess
import urllib.request
import urllib.error
from pathlib import Path

NAMESPACE = "monitoring"
DASHBOARD_FILE = Path("monitoring/grafana-dashboard.json")
GRAFANA_URL = "http://localhost:3000"

def secret(key):
    return subprocess.check_output([
        "kubectl", "get", "secret", "grafana-admin",
        "-n", NAMESPACE,
        "-o", f"jsonpath={{.data.{key}}}"
    ], text=True).strip()

import base64

username = base64.b64decode(secret("admin-user")).decode()
password = base64.b64decode(secret("admin-password")).decode()

def api(path, method="GET", payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(
        GRAFANA_URL + path,
        data=data,
        method=method,
        headers={
            "Authorization": "Basic " + base64.b64encode(
                f"{username}:{password}".encode()
            ).decode(),
            "Content-Type": "application/json"
        }
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read())

dashboard = json.loads(DASHBOARD_FILE.read_text())

assert dashboard.get("uid") == "adfvpk2", (
    "Dashboard UID mismatch. Refusing to update."
)

datasource = next(
    (p.get("datasource") for p in dashboard["panels"]
     if p.get("datasource", {}).get("type") == "prometheus"),
    None
)

if not datasource:
    raise RuntimeError("Prometheus datasource UID not found in existing panels.")

existing_titles = {p.get("title") for p in dashboard["panels"]}
next_id = max((p.get("id", 0) for p in dashboard["panels"]), default=0) + 1

def add_panel(title, expression, panel_type="timeseries",
              unit="short", width=12, height=8, legend=True):

    global next_id

    if title in existing_titles:
        print(f"Skipping existing panel: {title}")
        return

    index = len(dashboard["panels"])
    x = (index % 2) * 12
    y = 8 + ((index - 2) // 2) * 8

    panel = {
        "id": next_id,
        "title": title,
        "type": panel_type,
        "datasource": datasource,
        "gridPos": {
            "x": x, "y": y, "w": width, "h": height
        },
        "targets": [{
            "refId": "A",
            "expr": expression,
            "legendFormat": "{{namespace}} / {{pod}}",
            "range": True
        }],
        "fieldConfig": {
            "defaults": {
                "unit": unit,
                "color": {"mode": "palette-classic"},
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"color": "green", "value": None},
                        {"color": "red", "value": 80}
                    ]
                }
            },
            "overrides": []
        },
        "options": {
            "legend": {
                "showLegend": legend,
                "displayMode": "list",
                "placement": "bottom"
            },
            "tooltip": {"mode": "multi"}
        }
    }

    if panel_type == "stat":
        panel["options"] = {
            "reduceOptions": {
                "calcs": ["lastNotNull"],
                "fields": "",
                "values": False
            },
            "orientation": "auto",
            "textMode": "auto",
            "colorMode": "value",
            "graphMode": "area",
            "justifyMode": "auto"
        }

    dashboard["panels"].append(panel)
    existing_titles.add(title)
    next_id += 1
    print(f"Added: {title}")

# Cluster overview
add_panel("Total Nodes", "count(kube_node_info)", "stat", "short", 6, 4)
add_panel("Total Pods", "count(kube_pod_info)", "stat", "short", 6, 4)
add_panel(
    "Running Pods",
    'sum(kube_pod_status_phase{phase="Running"})',
    "stat", "short", 6, 4
)
add_panel(
    "Failed Pods",
    'sum(kube_pod_status_phase{phase="Failed"})',
    "stat", "short", 6, 4
)
add_panel(
    "Available Deployments",
    "sum(kube_deployment_status_replicas_available)",
    "stat", "short", 6, 4
)
add_panel(
    "Ready Nodes",
    'sum(kube_node_status_condition{condition="Ready",status="true"})',
    "stat", "short", 6, 4
)

# Workload monitoring
add_panel(
    "Pod CPU Usage",
    'sum by (namespace,pod) (rate(container_cpu_usage_seconds_total{container!="",container!="POD"}[5m]))',
    "timeseries", "cores"
)
add_panel(
    "Pod Memory Usage",
    'sum by (namespace,pod) (container_memory_working_set_bytes{container!="",container!="POD"})',
    "timeseries", "bytes"
)
add_panel(
    "Pod Status by Phase",
    "sum by (phase) (kube_pod_status_phase)",
    "timeseries", "short"
)
add_panel(
    "Deployment Desired vs Available",
    "sum by (namespace,deployment) (kube_deployment_spec_replicas)",
    "timeseries", "short"
)
add_panel(
    "Container Restarts (Last Hour)",
    "sum by (namespace,pod) (increase(kube_pod_container_status_restarts_total[1h]))",
    "timeseries", "short"
)

dashboard["title"] = "AKS Cluster Monitoring"
dashboard["refresh"] = "30s"
dashboard["time"] = {"from": "now-6h", "to": "now"}
dashboard["timezone"] = "browser"

payload = {
    "dashboard": dashboard,
    "folderId": 0,
    "overwrite": True,
    "message": "Expand AKS Kubernetes monitoring dashboard"
}

result = api("/api/dashboards/db", "POST", payload)

DASHBOARD_FILE.write_text(json.dumps(dashboard, indent=2) + "\n")

print("\n===== GRAFANA DASHBOARD UPDATED =====")
print("Title:", dashboard["title"])
print("UID:", result.get("uid"))
print("URL:", GRAFANA_URL + result.get("url", ""))
print("Panels:", len(dashboard["panels"]))
print("Version:", result.get("version"))
print("Saved:", DASHBOARD_FILE)
