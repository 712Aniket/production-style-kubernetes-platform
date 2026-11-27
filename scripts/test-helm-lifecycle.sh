#!/usr/bin/env bash
set -Eeuo pipefail

NAMESPACE="portfolio"
RELEASE="portfolio-frontend"
CONFIGMAP="portfolio-config"
URL="http://127.0.0.1:5001"

ORIGINAL_REVISION=""
UPGRADE_ATTEMPTED=0

rollback_release() {
    echo ""
    echo "===== ROLLBACK ====="

    if [[ -n "$ORIGINAL_REVISION" ]]; then
        helm rollback "$RELEASE" "$ORIGINAL_REVISION" \
            -n "$NAMESPACE" \
            --wait \
            --timeout 120s

        kubectl rollout status deployment/"$RELEASE" \
            -n "$NAMESPACE" --timeout=120s
    fi
}

handle_error() {
    EXIT_CODE=$?

    if [[ "$UPGRADE_ATTEMPTED" -eq 1 ]]; then
        echo "ERROR: Lifecycle test failed. Restoring original release."
        rollback_release || echo "WARNING: Automatic rollback needs attention."
    fi

    exit "$EXIT_CODE"
}

trap handle_error ERR

echo "======================================"
echo " Helm Upgrade and Rollback Test"
echo "======================================"

echo "[1/8] Checking current Helm release..."

ORIGINAL_REVISION=$(
    helm history "$RELEASE" -n "$NAMESPACE" -o json |
    python3 -c '
import json, sys
history = json.load(sys.stdin)
deployed = [r for r in history if r["status"] == "deployed"]
if not deployed:
    raise SystemExit("No deployed Helm revision found")
print(deployed[-1]["revision"])
'
)

echo "Original revision: $ORIGINAL_REVISION"

CURRENT_LOG_LEVEL=$(kubectl get configmap "$CONFIGMAP" \
    -n "$NAMESPACE" \
    -o jsonpath='{.data.LOG_LEVEL}')

echo "Current LOG_LEVEL: $CURRENT_LOG_LEVEL"

if [[ "$CURRENT_LOG_LEVEL" != "info" ]]; then
    echo "Unexpected initial LOG_LEVEL. Stopping without changes."
    exit 1
fi

echo "[2/8] Checking current application..."

HTTP_CODE=$(curl -sS -o /dev/null -w '%{http_code}' "$URL")
[[ "$HTTP_CODE" == "200" ]]

echo "Current HTTP response: $HTTP_CODE"

echo "[3/8] Performing controlled Helm upgrade..."

UPGRADE_ATTEMPTED=1

helm upgrade "$RELEASE" helm/portfolio-frontend \
    -n "$NAMESPACE" \
    --set config.LOG_LEVEL=debug \
    --force-conflicts \
    --wait \
    --timeout 120s

echo "[4/8] Verifying upgraded configuration..."

UPDATED_LOG_LEVEL=$(kubectl get configmap "$CONFIGMAP" \
    -n "$NAMESPACE" \
    -o jsonpath='{.data.LOG_LEVEL}')

echo "Updated LOG_LEVEL: $UPDATED_LOG_LEVEL"
[[ "$UPDATED_LOG_LEVEL" == "debug" ]]

echo "[5/8] Verifying frontend replicas..."

kubectl rollout status deployment/"$RELEASE" \
    -n "$NAMESPACE" --timeout=120s

READY=$(kubectl get deployment "$RELEASE" \
    -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}')

[[ "$READY" == "2" ]]

echo "Ready replicas: $READY/2"

echo "[6/8] Running Helm test..."

helm test "$RELEASE" -n "$NAMESPACE" --logs

echo "[7/8] Checking application HTTP response..."

HTTP_CODE=$(curl -sS -o /dev/null -w '%{http_code}' "$URL")
[[ "$HTTP_CODE" == "200" ]]

echo "HTTP response: $HTTP_CODE"

echo "[8/8] Rolling back to original revision..."

rollback_release

UPGRADE_ATTEMPTED=0

RESTORED_LOG_LEVEL=$(kubectl get configmap "$CONFIGMAP" \
    -n "$NAMESPACE" \
    -o jsonpath='{.data.LOG_LEVEL}')

[[ "$RESTORED_LOG_LEVEL" == "info" ]]

FINAL_HTTP_CODE=$(curl -sS -o /dev/null -w '%{http_code}' "$URL")
[[ "$FINAL_HTTP_CODE" == "200" ]]

echo ""
echo "======================================"
echo " HELM LIFECYCLE TEST PASSED"
echo "======================================"
echo "Original revision: $ORIGINAL_REVISION"
echo "Restored LOG_LEVEL: $RESTORED_LOG_LEVEL"
echo "Final HTTP response: $FINAL_HTTP_CODE"

helm history "$RELEASE" -n "$NAMESPACE"
