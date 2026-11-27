#!/usr/bin/env bash
set -Eeuo pipefail

RG="rg-project3-aks"
CLUSTER="aks-project3-platform"

echo "Project 3 - AKS startup"

az account show >/dev/null

az aks start -g "$RG" -n "$CLUSTER"

echo "Waiting for AKS control plane..."
for i in $(seq 1 60); do
    STATE=$(az aks show -g "$RG" -n "$CLUSTER" --query powerState.code -o tsv)
    [[ "$STATE" == "Running" ]] && break
    sleep 15
done

[[ "${STATE:-}" == "Running" ]] || {
    echo "AKS did not reach Running state in time."
    exit 1
}

echo "Refreshing Kubernetes credentials..."
az aks get-credentials -g "$RG" -n "$CLUSTER" --overwrite-existing

echo "Waiting for worker nodes..."
kubectl wait --for=condition=Ready nodes --all --timeout=15m

echo "Waiting for application and monitoring deployments..."
kubectl rollout status deployment/portfolio-frontend -n portfolio --timeout=10m
kubectl rollout status deployment/grafana -n monitoring --timeout=10m
kubectl rollout status deployment/prometheus-server -n monitoring --timeout=10m
kubectl rollout status deployment/prometheus-kube-state-metrics -n monitoring --timeout=10m

echo
echo "Project 3 infrastructure is ready."
kubectl get nodes
kubectl get deployments -n portfolio
kubectl get deployments -n monitoring
echo
echo "Grafana access: kubectl port-forward svc/grafana 3000:80 -n monitoring"
echo "Prometheus access: kubectl port-forward svc/prometheus-server 9090:80 -n monitoring"
