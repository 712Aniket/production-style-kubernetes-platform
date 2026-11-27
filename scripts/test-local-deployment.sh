#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="portfolio"
RELEASE="portfolio-frontend"
DEPLOYMENT="portfolio-frontend"
URL="http://127.0.0.1:5001"

echo "======================================"
echo " Local Kubernetes Deployment Tests"
echo "======================================"

echo "[1/7] Checking Kubernetes node..."
kubectl wait --for=condition=Ready node/minikube --timeout=60s

echo "[2/7] Validating Helm chart..."
helm lint helm/portfolio-frontend

echo "[3/7] Checking Helm release..."
HELM_STATUS="$(helm status "$RELEASE" -n "$NAMESPACE")"

if [[ "$HELM_STATUS" != *"STATUS: deployed"* ]]; then
    echo "FAIL: Helm release is not deployed."
    exit 1
fi

echo "Helm release is deployed."

echo "[4/7] Checking deployment replicas..."
READY=$(kubectl get deployment "$DEPLOYMENT" -n "$NAMESPACE" \
  -o jsonpath='{.status.readyReplicas}')

DESIRED=$(kubectl get deployment "$DEPLOYMENT" -n "$NAMESPACE" \
  -o jsonpath='{.spec.replicas}')

echo "Ready replicas: ${READY:-0}/${DESIRED}"

if [[ "${READY:-0}" != "$DESIRED" || "$DESIRED" != "2" ]]; then
    echo "FAIL: Expected 2 ready replicas."
    exit 1
fi

echo "[5/7] Checking frontend service..."
kubectl get endpoints "$DEPLOYMENT" -n "$NAMESPACE"

echo "[6/7] Running Helm test..."
helm test "$RELEASE" -n "$NAMESPACE" --logs

echo "[7/7] Checking HTTP response..."
HTTP_CODE=$(curl -sS -o /dev/null -w '%{http_code}' "$URL")

if [[ "$HTTP_CODE" != "200" ]]; then
    echo "FAIL: HTTP response was $HTTP_CODE"
    exit 1
fi

echo "HTTP response: $HTTP_CODE"

echo "======================================"
echo " ALL LOCAL DEPLOYMENT TESTS PASSED"
echo "======================================"
