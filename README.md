# Production-Style Kubernetes Platform

A production-oriented Kubernetes platform deployed on **Azure Kubernetes Service (AKS)** using Terraform, Docker, Helm, Prometheus and Grafana.

## Project status

**Status: In progress — core deployment and reliability demonstrations completed; final verification and documentation are pending.**

This project provisions and operates a containerized frontend on AKS, packages the application with Helm, applies Kubernetes reliability and scaling controls, and exposes cluster/application metrics through Prometheus and Grafana.

## Technology stack

- **Cloud:** Microsoft Azure
- **Kubernetes:** Azure Kubernetes Service (AKS)
- **Infrastructure as Code:** Terraform
- **Containerization:** Docker
- **Packaging and release management:** Helm
- **Monitoring:** Prometheus and Grafana
- **Application image:** `ghcr.io/712aniket/production-style-kubernetes-platform`

## Implemented platform capabilities

- AKS cluster provisioned with Terraform.
- Frontend deployed to the `portfolio` namespace.
- Helm chart used to manage the frontend release.
- Horizontal Pod Autoscaler configured with a minimum of 2 and maximum of 5 replicas, targeting 60% CPU utilization.
- Readiness and liveness HTTP probes configured for the frontend.
- Kubernetes resource requests and limits configured.
- Prometheus and Grafana deployed for cluster/platform observability.
- Start/stop helper scripts provided for the AKS project environment.

## Reliability and lifecycle test results

| Test | Result | Evidence / notes |
|---|---|---|
| HPA scale-out | **Passed** | Load test caused replicas to scale out to 5. |
| HPA scale-down | **Passed** | After load stopped and the stabilization period elapsed, replicas returned to 2. |
| Pod self-healing | **Passed** | A frontend pod was deleted; the ReplicaSet created a replacement and the replacement became Ready. |
| Readiness probe failure | **Demonstrated** | Readiness endpoint was temporarily changed to `/readiness-test-fail`; the affected pod remained Running but NotReady. |
| Liveness probe failure | **Not executed** | Not included in the completed test evidence. The liveness probe is configured in the deployment. |
| Helm upgrade | **Passed** | Release upgraded successfully to revision 6 using client-side apply (`--server-side=false`). Deployment subsequently showed 2/2 available replicas. |
| Helm rollback | **Command succeeded** | Rolled back to revision 3. Helm history showed revision 7 deployed with description `Rollback to 3`. Post-rollback workload health should be checked as part of final verification. |

> The readiness failure was a deliberate test condition, not the intended steady state. The Helm upgrade completed successfully after switching to client-side apply. The subsequent rollback returned the Helm release to revision 3.

## Evidence

Screenshots are maintained in:

`docs/evidence/05-testing-reliability/screenshots/`

Current evidence set (use the filenames present in the repository; not every test has a screenshot):

- `01-hpa-scale-out.png`
- `02-hpa-scale-down.png`
- `03-pod-self-healing.png`
- `05-readiness-probe-failure.png`
- `07-ghcr-image-published.png`
- `08-helm-rollback.png`

A separate liveness-probe screenshot was not captured because that test was not executed. Do not interpret a missing screenshot as a passing test.

## Repository layout

- `helm/portfolio-frontend/` — Helm chart for the frontend workload.
- `terraform/` — Terraform infrastructure configuration.
- `scripts/` — deployment, lifecycle validation and AKS start/stop helper scripts.
- `docs/evidence/` — project evidence and test screenshots.

## Useful operational commands

Check the frontend deployment and pods:

```bash
kubectl get deployment portfolio-frontend -n portfolio
kubectl get pods -n portfolio -l app=portfolio-frontend
```

Inspect the Helm release history:

```bash
helm history portfolio-frontend -n portfolio
```

Check HPA status:

```bash
kubectl get hpa -n portfolio
```

## Remaining work

- Perform final post-rollback deployment, pod, probe and HPA health verification.
- Review and organize the complete evidence set.
- Record final validation results and project completion status.

## Important

This project uses Azure resources that may incur charges. Stop the AKS cluster when it is not needed, while remembering that attached disks, public IP addresses and load balancers may continue to incur costs.
