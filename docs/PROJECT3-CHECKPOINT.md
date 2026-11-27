# Project 3 - Kubernetes Platform Engineering

Checkpoint date: 28 November 2026

## Completed

- AKS cluster deployed and operational.
- Frontend deployed and managed through Helm.
- Docker image published to GitHub Container Registry (GHCR).
- HPA configured with CPU target 60%, minimum 2 and maximum 5 replicas.
- HPA scale-out validated up to 5 replicas.
- HPA scale-down validated back to 2 replicas.
- Pod self-healing validated after pod deletion.
- Readiness probe failure scenario demonstrated.
- Helm upgrade completed successfully.
- Helm rollback completed successfully; revision 7 deployed.
- Post-rollback deployment health verified: 2/2 available.
- Frontend HTTP response verified: HTTP 200.
- Readiness probe path verified: `/`.
- Prometheus and Grafana operational.
- AKS Kubernetes Operations dashboard validated with live metrics.
- Dashboard showed 1 ready node, 20 running pods, 0 failed pods and 5 healthy deployments.
- Terraform import and plan validation completed with no changes.

## Reliability Test Results

| Test | Result |
|---|---|
| HPA scale-out | PASS |
| HPA scale-down | PASS |
| Pod self-healing | PASS |
| Readiness probe failure | PASS |
| Liveness probe failure | Not executed |
| Helm upgrade | PASS |
| Helm rollback | PASS |
| Frontend HTTP check | PASS - HTTP 200 |
| Readiness path | PASS - `/` |
| Grafana metrics validation | PASS |

## Remaining Closeout Tasks

1. Save final Grafana and rollback evidence.
2. Review and update README documentation.
3. Verify Git changes and push only approved project files.
4. Review Azure resources and stop AKS when finished to control costs.

## Scope and Constraints

- Azure AKS only. Do not introduce Minikube.
- Preserve Project 1 and Project 2 resources.
- Avoid unnecessary Azure spending.
- Do not commit Terraform state, secrets or temporary files.

## Project Status

Core platform implementation and major reliability validations are complete.
Final documentation, evidence collection and Azure cleanup remain.
