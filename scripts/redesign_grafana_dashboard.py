import base64
import copy
import json
import subprocess
import urllib.request

FILE = "monitoring/grafana-dashboard.json"
GRAFANA_URL = "http://localhost:3000"
DASHBOARD_UID = "adfvpk2"

def secret(key):
    value = subprocess.check_output([
        "kubectl", "get", "secret", "grafana-admin",
        "-n", "monitoring", "-o", f"jsonpath={{.data.{key}}}"
    ], text=True).strip()
    return base64.b64decode(value).decode()

auth = base64.b64encode(
    f"{secret('admin-user')}:{secret('admin-password')}".encode()
).decode()

with open(FILE) as f:
    dashboard = json.load(f)

assert dashboard["uid"] == DASHBOARD_UID, "Unexpected dashboard UID"

panels = {p["title"]: p for p in dashboard["panels"]}

# Correct KPI: count deployments whose available replicas meet desired replicas.
panels["Available Deployments"]["targets"][0]["expr"] = (
    'count((kube_deployment_status_replicas_available '
    '>= on(namespace,deployment) kube_deployment_spec_replicas) == 1)'
)

panels["Available Deployments"]["title"] = "Healthy Deployments"

# Desired vs Available: show both series.
p = panels["Deployment Desired vs Available"]
p["targets"] = [
    {
        "refId": "A",
        "expr": "sum by (namespace,deployment) (kube_deployment_spec_replicas)",
        "legendFormat": "{{namespace}}/{{deployment}} Desired"
    },
    {
        "refId": "B",
        "expr": "sum by (namespace,deployment) (kube_deployment_status_replicas_available)",
        "legendFormat": "{{namespace}}/{{deployment}} Available"
    }
]

# More meaningful title and units.
panels["Total Nodes"]["title"] = "Cluster Nodes"
panels["Total Pods"]["title"] = "Total Pods"
panels["Running Pods"]["title"] = "Running Pods"
panels["Failed Pods"]["title"] = "Failed Pods"
panels["Ready Nodes"]["title"] = "Ready Nodes"

# Dashboard layout: 24-column grid.
layout = {
    "Total Nodes": (0, 0, 4, 4),
    "Ready Nodes": (4, 0, 4, 4),
    "Total Pods": (8, 0, 4, 4),
    "Running Pods": (12, 0, 4, 4),
    "Failed Pods": (16, 0, 4, 4),
    "Available Deployments": (20, 0, 4, 4),

    "Node CPU Usage": (0, 5, 12, 8),
    "Node Memory Utilization": (12, 5, 12, 8),

    "Pod CPU Usage": (0, 13, 12, 8),
    "Pod Memory Usage": (12, 13, 12, 8),

    "Pod Status by Phase": (0, 21, 8, 9),
    "Deployment Desired vs Available": (8, 21, 10, 9),
    "Container Restarts (Last Hour)": (18, 21, 6, 9),
}

for title, (x, y, w, h) in layout.items():
    panel = panels[title]
    panel["gridPos"] = {"x": x, "y": y, "w": w, "h": h}

    if panel["type"] == "stat":
        panel["options"] = {
            "colorMode": "background",
            "graphMode": "area",
            "justifyMode": "center",
            "orientation": "auto",
            "reduceOptions": {
                "calcs": ["lastNotNull"],
                "fields": "",
                "values": False
            },
            "textMode": "auto"
        }
        panel["fieldConfig"]["defaults"]["thresholds"] = {
            "mode": "absolute",
            "steps": [
                {"color": "green", "value": None},
                {"color": "yellow", "value": 1}
            ]
        }

    else:
        panel["fieldConfig"]["defaults"]["custom"] = {
            "drawStyle": "line",
            "lineInterpolation": "smooth",
            "lineWidth": 2,
            "fillOpacity": 12,
            "showPoints": "never",
            "spanNulls": False
        }
        panel["options"] = {
            "legend": {
                "displayMode": "table",
                "placement": "bottom",
                "showLegend": True
            },
            "tooltip": {"mode": "multi", "sort": "desc"}
        }

# Special status colours for failed pods and restarts.
for title in ("Failed Pods", "Container Restarts (Last Hour)"):
    panel = panels[title]
    panel["fieldConfig"]["defaults"]["thresholds"] = {
        "mode": "absolute",
        "steps": [
            {"color": "green", "value": None},
            {"color": "red", "value": 1}
        ]
    }

# Improve dashboard presentation.
dashboard["title"] = "AKS | Kubernetes Operations"
dashboard["description"] = (
    "Cluster health, resource utilization and workload operations."
)
dashboard["refresh"] = "30s"
dashboard["time"] = {"from": "now-6h", "to": "now"}
dashboard["timezone"] = "browser"
dashboard["editable"] = True
dashboard["graphTooltip"] = 2
dashboard["panels"] = list(panels.values())

with open(FILE, "w") as f:
    json.dump(dashboard, f, indent=2)

payload = json.dumps({
    "dashboard": dashboard,
    "overwrite": True,
    "message": "Redesign Kubernetes operations dashboard"
}).encode()

request = urllib.request.Request(
    f"{GRAFANA_URL}/api/dashboards/db",
    data=payload,
    headers={
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json"
    },
    method="POST"
)

with urllib.request.urlopen(request, timeout=30) as response:
    result = json.load(response)

print("Grafana dashboard updated successfully.")
print("Title:", dashboard["title"])
print("UID:", dashboard["uid"])
print("Panels:", len(dashboard["panels"]))
print("URL:", f"{GRAFANA_URL}/d/{DASHBOARD_UID}/")
print("API status:", result.get("status"))
