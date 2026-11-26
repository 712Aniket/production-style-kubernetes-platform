import json
from pathlib import Path

# Epic -> Features -> two implementation stories per feature
plan = {
"Project Foundation & Architecture": [
"Define project scope and requirements",
"Design platform architecture",
"Establish engineering standards"
],
"GitHub Repository & Source Control": [
"Create and structure GitHub repository",
"Implement Git branching and versioning",
"Establish repository backup and recovery"
],
"Local Development Environment": [
"Configure WSL and development tools",
"Configure Docker development environment",
"Install and configure Minikube"
],
"Docker & Containerization": [
"Design application container architecture",
"Build optimized Docker images",
"Implement container security practices"
],
"Kubernetes & Minikube": [
"Design multi-node Minikube cluster",
"Deploy Kubernetes workloads",
"Configure Kubernetes networking and storage"
],
"Terraform & Infrastructure Automation": [
"Design Terraform project structure",
"Implement reusable Terraform configurations",
"Validate infrastructure automation"
],
"Helm & Application Packaging": [
"Create Helm chart structure",
"Implement configurable Helm deployments",
"Manage Helm releases and rollback"
],
"Azure DevOps CI/CD": [
"Connect GitHub with Azure DevOps",
"Configure Azure DevOps self-hosted agent",
"Build automated CI pipelines",
"Implement automated Kubernetes CD pipelines",
"Add pipeline security and approvals"
],
"Monitoring & Observability": [
"Deploy Prometheus monitoring",
"Configure Grafana dashboards",
"Implement application and cluster monitoring"
],
"Security & Governance": [
"Implement Kubernetes RBAC",
"Configure secrets and configuration security",
"Implement network policies",
"Perform container and dependency security scanning"
],
"Testing & Reliability": [
"Implement application and deployment testing",
"Test Kubernetes failure recovery",
"Validate scaling and resource limits"
],
"Documentation, Operations & Cost Management": [
"Create architecture and deployment documentation",
"Create troubleshooting and operational runbooks",
"Implement backup and disaster recovery procedures",
"Establish cost monitoring and project governance"
]
}

catalog = []
counts = {"Epic": 0, "Feature": 0, "User Story": 0, "Task": 0}

def add(item_type, title, description, parent=None, acceptance=None):
    item = {
        "type": item_type,
        "title": title,
        "description": description,
        "parent": parent,
        "tags": ["Project3", "Planning"]
    }
    if acceptance:
        item["acceptance_criteria"] = acceptance
    catalog.append(item)
    counts[item_type] += 1
    return title

for epic_title, features in plan.items():
    epic = add("Epic", epic_title,
               f"Deliver the Project 3 capability: {epic_title}. "
               "Local-first Kubernetes Platform Engineering project.")

    for feature_title in features:
        feature = add("Feature", feature_title,
                      f"Deliver and verify {feature_title.lower()}.", epic)

        story_specs = [
            ("Design", f"Design and plan {feature_title.lower()}"),
            ("Implement", f"Implement and validate {feature_title.lower()}")
        ]

        for action, story_title in story_specs:
            story = add(
                "User Story", story_title,
                f"As a platform engineer, I want to {story_title.lower()} "
                "so that the platform is maintainable, secure and repeatable.",
                feature,
                "Implementation is documented, tested and supported by "
                "verifiable evidence."
            )

            add("Task", f"Document requirements and approach for: {story_title}",
                "Record scope, prerequisites, design decisions and expected outcome.",
                story)
            add("Task", f"Execute and verify: {story_title}",
                "Perform the work, run relevant checks and record evidence.",
                story)

output = {
    "project": "Kubernetes-Platform-Engineering",
    "organization": "712aniket",
    "source": "Project 3 approved planning direction",
    "status": "Planning - not yet uploaded to Azure DevOps",
    "hierarchy": "Epic > Feature > User Story > Task",
    "counts": counts,
    "total": len(catalog),
    "items": catalog
}

path = Path("config/work_item_catalog.json")
path.write_text(json.dumps(output, indent=2), encoding="utf-8")

print("===== PROJECT 3 BACKLOG CATALOGUE =====")
for kind, count in counts.items():
    print(f"{kind}: {count}")
print(f"TOTAL WORK ITEMS: {len(catalog)}")
print(f"Saved: {path}")
print("Azure DevOps changes: NONE")
