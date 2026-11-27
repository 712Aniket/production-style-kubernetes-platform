#!/usr/bin/env bash
set -Eeuo pipefail

RG="rg-project3-aks"
CLUSTER="aks-project3-platform"

echo "Project 3 - AKS shutdown"
echo "Cluster: $CLUSTER"
echo "No resources will be deleted."

read -r -p "Stop AKS and reduce compute costs? (yes/no): " CONFIRM
[[ "$CONFIRM" == "yes" ]] || { echo "Cancelled."; exit 0; }

az account show >/dev/null

STATE=$(az aks show -g "$RG" -n "$CLUSTER" --query powerState.code -o tsv)

if [[ "$STATE" == "Stopped" ]]; then
    echo "AKS is already stopped."
    exit 0
fi

az aks stop -g "$RG" -n "$CLUSTER"

echo "Waiting for AKS to stop..."
for i in $(seq 1 60); do
    STATE=$(az aks show -g "$RG" -n "$CLUSTER" --query powerState.code -o tsv)
    [[ "$STATE" == "Stopped" ]] && {
        echo "AKS stopped successfully."
        exit 0
    }
    sleep 15
done

echo "Timed out waiting for AKS to stop. Check Azure portal."
exit 1
