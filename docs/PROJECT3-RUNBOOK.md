# Project 3 – Kubernetes Platform Engineering Runbook

## 1. Platform Overview

This project implements a Kubernetes application platform on Microsoft Azure AKS.

Deployment architecture:

1. Developer pushes code to GitHub.
2. GitHub Actions validates Kubernetes manifests and Helm charts.
3. Docker builds the application image.
4. Trivy scans the image for vulnerabilities.
5. GitHub Actions publishes the image to GHCR.
6. GitHub Actions updates the image SHA in the GitOps Helm values file.
7. Argo CD detects the Git change.
8. Argo CD synchronizes the application to AKS.
9. Kubernetes maintains the desired application replicas.

Argo CD is the sole application deployment controller.

## 2. Infrastructure Details

| Component | Configuration |
|---|---|
| Azure Resource Group | rg-project3-aks |
| AKS Cluster | aks-project3-platform |
| Region | centralindia |
| Namespace | portfolio |
| Helm Release | portfolio-frontend |
| Deployment | portfolio-frontend |
| Service | portfolio-frontend |
| HPA | portfolio-frontend |
| Argo CD Application | portfolio-frontend |
| Container Registry | ghcr.io/712aniket/production-style-kubernetes-platform |

## 3. Authentication and Access

AKS uses Microsoft Entra authentication and Azure RBAC.

GitHub Actions uses OIDC integration for Azure authentication where required.

Local administration:

- Authenticate through Azure CLI.
- Obtain AKS credentials.
- Convert kubeconfig authentication using kubelogin.
- Verify Kubernetes access before making changes.

Never commit credentials, tokens, private keys, or Kubernetes secrets.

## 4. Normal Deployment Procedure

1. Make application changes.
2. Review the changes.
3. Push to the main branch.
4. Verify GitHub Actions validation.
5. Review the Trivy security report.
6. Confirm successful GHCR image publishing.
7. Confirm the GitOps job updates the Helm image SHA.
8. Check Argo CD synchronization.
9. Verify AKS deployment rollout.
10. Verify application HTTP response.

Do not use direct Helm deployment while Argo CD owns the application.

## 5. Health Checks

Check Argo CD:

    kubectl get application portfolio-frontend -n argocd

Check deployment:

    kubectl get deployment portfolio-frontend -n portfolio

Check pods:

    kubectl get pods -n portfolio

Check service:

    kubectl get service portfolio-frontend -n portfolio

Check autoscaling:

    kubectl get hpa -n portfolio

Check rollout:

    kubectl rollout status deployment/portfolio-frontend -n portfolio

Expected healthy state:

- Argo CD: Synced and Healthy.
- Deployment: Desired replicas available.
- Pods: Running and Ready.
- No unexpected container restarts.
- HPA configured for 2–5 replicas.

## 6. GitOps Troubleshooting

If Argo CD reports OutOfSync:

1. Inspect the Application status.
2. Check the repository revision.
3. Verify the image SHA in the Helm values file.
4. Check repository connectivity.
5. Inspect synchronization errors.
6. Correct the Git source and allow reconciliation.

If the application becomes Degraded:

1. Inspect Deployment status.
2. Inspect pod events.
3. Check container logs.
4. Verify image availability in GHCR.
5. Check image pull configuration.
6. Correct the underlying issue and allow Argo CD to reconcile.

## 7. Rollback Procedure

Argo CD manages the desired application state.

1. Identify the last known-good Git revision and image SHA.
2. Revert the GitOps image-tag change in Git.
3. Push the approved rollback commit.
4. Allow Argo CD to synchronize.
5. Verify the previous image is deployed.
6. Check pod readiness and application response.
7. Record the rollback revision and reason.

Avoid relying on a direct Helm rollback as the permanent solution because Argo CD may reconcile the cluster back to Git.

## 8. Security Controls

Implemented:

- Trivy image vulnerability scanning in CI.
- GitHub Actions OIDC integration with Azure.
- Azure RBAC.
- Microsoft Entra authentication for AKS.
- Argo CD automated reconciliation.
- Argo CD self-healing test for a Helm-managed ConfigMap field.

Requires further verification or implementation:

- Secret exposure and Git history audit.
- Non-root container execution.
- Container security context.
- Kubernetes NetworkPolicies.
- Strict vulnerability blocking thresholds.
- Admission controls.
- Liveness probe failure testing.
- Image and dependency update policies.

Important: Trivy currently uses exit-code 0. Vulnerability findings are reported but do not fail the pipeline.

## 9. Monitoring and Reliability

Monitoring uses Azure-managed Prometheus and Grafana.

Previously validated:

- HPA scale-out and scale-down.
- Pod self-healing.
- Readiness probe failure handling.
- Helm upgrade and rollback.
- Grafana dashboard metrics.
- Argo CD self-healing for a Helm-managed ConfigMap field.

Liveness probe failure simulation remains untested.

## 10. Cost Management

Azure resources may continue to incur charges even when application pods are stopped.

Before stopping or deleting infrastructure:

1. Review AKS costs.
2. Review monitoring and managed-service costs.
3. Check persistent disks and retained resources.
4. Capture required evidence.
5. Preserve configuration and documentation.
6. Obtain approval before deleting resources.

## 11. Evidence to Retain

Maintain evidence of:

- Successful GitHub Actions runs.
- GHCR image publication.
- GitOps image-tag update.
- Argo CD Synced and Healthy status.
- AKS deployment and pod status.
- HPA testing.
- Helm rollback testing.
- Grafana validation.
- Security scan reports.

## 12. Current Project Status

The automated CI and GitOps delivery pipeline is operational.

The latest verified deployment showed:

- GitOps image SHA matched the deployed AKS image SHA.
- Argo CD reported Synced and Healthy.
- Two application pods were Running and Ready.
- Both pods had zero restarts.

Final documentation publication, Azure Boards status reconciliation, and additional security hardening remain outstanding.
