# Project 3 - Progress Checkpoint

Checkpoint date: Fri Nov 27 18:37:15 UTC 2026

## Completed
- AKS cluster deployed and operational.
- Frontend deployed through Helm.
- HPA configured: CPU target 60%, minimum 2, maximum 5 replicas.
- Prometheus and Grafana operational.
- Grafana dashboard updated with four HPA panels.
- Terraform import and plan validation completed with no changes.
- Initial controlled HTTP load test completed.

## Load Test Result
- Load generator completed successfully.
- Frontend CPU approximately 3m per pod.
- HPA remained at 2 replicas; target CPU 60%.
- HTTP load was insufficient to trigger scale-out.
- Autoscaling under load is NOT yet validated.

## Next Steps
1. Run a controlled CPU-intensive test while monitoring Grafana.
2. Verify HPA scale-out and scale-down.
3. Test pod self-healing.
4. Validate readiness and liveness probes.
5. Complete Helm rollback validation.
6. Complete CI/CD, GitOps and security checks.
7. Capture final evidence and review cloud resource cleanup.

## Important
- AKS only. Do not introduce Minikube.
- Preserve Project 1 and Project 2 resources.
- Avoid unnecessary Azure spending.
