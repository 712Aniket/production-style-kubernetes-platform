import copy
import base64
import json
import subprocess
import urllib.request

FILE = "monitoring/grafana-dashboard.json"
URL = "http://localhost:3000"
UID = "adfvpk2"

def get_secret(key):
    value = subprocess.check_output([
        "kubectl", "get", "secret", "grafana-admin",
        "-n", "monitoring", "-o", f"jsonpath={{.data.{key}}}"
    ], text=True).strip()
    return base64.b64decode(value).decode()

auth = base64.b64encode(
    f"{get_secret('admin-user')}:{get_secret('admin-password')}".encode()
).decode()

with open(FILE) as f:
    dashboard = json.load(f)

assert dashboard["uid"] == UID

panels = {p["id"]: p for p in dashboard["panels"]}

required = set(range(1, 14))
missing = required - set(panels)
if missing:
    raise RuntimeError(f"Missing expected panel IDs: {sorted(missing)}")

# KPI cards: IDs 3–8
for panel_id in range(3, 9):
    p = panels[panel_id]
    p.setdefault("options", {})["colorMode"] = "value"
    p["options"]["graphMode"] = "none"
    p["fieldConfig"]["defaults"]["thresholds"] = {
        "mode": "absolute",
        "steps": [{"color": "green", "value": None}]
    }

# Failed Pods: green at zero, red above zero.
panels[6]["fieldConfig"]["defaults"]["thresholds"] = {
    "mode": "absolute",
    "steps": [
        {"color": "green", "value": None},
        {"color": "red", "value": 1}
    ]
}

# Pod CPU: show only the eight busiest pods.
panels[9]["targets"][0]["expr"] = (
    'topk(8, sum by (namespace,pod) '
    '(rate(container_cpu_usage_seconds_total'
    '{container!="",container!="POD"}[5m])))'
)

# Pod memory: show only the eight largest consumers.
panels[10]["targets"][0]["expr"] = (
    'topk(8, sum by (namespace,pod) '
    '(container_memory_working_set_bytes'
    '{container!="",container!="POD"}))'
)

# Pod status: aggregate by phase.
panels[11]["targets"][0]["expr"] = (
    "sum by (phase) (kube_pod_status_phase)"
)

# Deployment replicas: compare desired and available by namespace.
panels[12]["targets"] = [
    {
        "refId": "A",
        "expr": "sum by (namespace) (kube_deployment_spec_replicas)",
        "legendFormat": "{{namespace}} Desired"
    },
    {
        "refId": "B",
        "expr": "sum by (namespace) (kube_deployment_status_replicas_available)",
        "legendFormat": "{{namespace}} Available"
    }
]

# Container restarts: top five affected pods.
panels[13]["targets"][0]["expr"] = (
    'topk(5, sum by (namespace,pod) '
    '(increase(kube_pod_container_status_restarts_total[1h])))'
)


# HPA AUTOSCALING PANELS
hpa_filter = '{namespace="portfolio",horizontalpodautoscaler="portfolio-frontend"}'

hpa_panels = [
    (14, "HPA Current Replicas",
     f"kube_horizontalpodautoscaler_status_current_replicas{hpa_filter}",
     "short", 0),
    (15, "HPA Desired Replicas",
     f"kube_horizontalpodautoscaler_status_desired_replicas{hpa_filter}",
     "short", 6),
    (16, "HPA Target CPU Utilization",
     'kube_horizontalpodautoscaler_spec_target_metric{namespace="portfolio",horizontalpodautoscaler="portfolio-frontend",metric_name="cpu",metric_target_type="utilization"}',
     "percent", 12),
]

for pid, title, expr, unit, x in hpa_panels:
    if pid not in panels:
        p = copy.deepcopy(panels[3])
        p.update({"id": pid, "title": title})
        p["gridPos"] = {"x": x, "y": 30, "w": 6, "h": 5}
        p["targets"] = [{"refId": "A", "expr": expr, "range": False}]
        p["fieldConfig"]["defaults"]["unit"] = unit
        dashboard["panels"].append(p)

if 17 not in panels:
    p = copy.deepcopy(panels[1])
    p.update({"id": 17, "title": "HPA Replica Limits"})
    p["gridPos"] = {"x": 18, "y": 30, "w": 6, "h": 5}
    p["targets"] = [
        {"refId": "A", "expr": 'kube_horizontalpodautoscaler_spec_min_replicas{namespace="portfolio"}', "legendFormat": "Minimum"},
        {"refId": "B", "expr": 'kube_horizontalpodautoscaler_spec_max_replicas{namespace="portfolio"}', "legendFormat": "Maximum"}
    ]
    p["fieldConfig"]["defaults"]["unit"] = "short"
    dashboard["panels"].append(p)

# Cleaner chart legends and tooltips.
for p in dashboard["panels"]:
    if p["type"] != "stat":
        p.setdefault("options", {})["legend"] = {
            "displayMode": "list",
            "placement": "bottom",
            "showLegend": True
        }
        p["options"]["tooltip"] = {
            "mode": "multi",
            "sort": "desc"
        }

with open(FILE, "w") as f:
    json.dump(dashboard, f, indent=2)

payload = json.dumps({
    "dashboard": dashboard,
    "overwrite": True,
    "message": "Refine Kubernetes dashboard visuals and queries"
}).encode()

req = urllib.request.Request(
    f"{URL}/api/dashboards/db",
    data=payload,
    headers={
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json"
    },
    method="POST"
)

with urllib.request.urlopen(req, timeout=30) as response:
    result = json.load(response)

print("Dashboard refinement published.")
print("Title:", dashboard["title"])
print("Panels:", len(dashboard["panels"]))
print("Status:", result.get("status"))
print("URL:", f"{URL}/d/{UID}/")
