#!/usr/bin/env bash

set -euo pipefail

EXPORTER_COUNT=${EXPORTER_COUNT:-5}
EXPORTER_PREFIX="qemu-exporter-"
JUMPSTART_NAMESPACE="auto-jumpstarter"

FAILED=()

for i in $(seq 0 "$EXPORTER_COUNT"); do
  EXPORTER_NAME=$(printf "%s%1d" "$EXPORTER_PREFIX" "$i")
  echo "Deleting exporter $EXPORTER_NAME"

  oc delete exporter "$EXPORTER_NAME" -n "$JUMPSTART_NAMESPACE"

  sleep 1
done

echo "Done: exporters deleted."
