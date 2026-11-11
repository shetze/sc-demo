#!/usr/bin/env bash

set -e

if [ "$#" -ne 1 ]; then
  echo "Usage: $(basename "$0") <username>" >&2
  echo "  username: the user to create the devspaces namespace for (must run as cluster-admin)." >&2
  exit 1
fi

USER_NAME=$1

oc get user "$USER_NAME" &>/dev/null || {
  echo "User $USER_NAME not found" >&2
  exit 1
}

# Create a devspaces namespace
NAMESPACE="devspaces-$USER_NAME"
echo "NAMESPACE: $NAMESPACE"

oc create -f - <<-EOF
kind: Namespace
apiVersion: v1
metadata:
  name: $NAMESPACE
  labels:
    app.kubernetes.io/part-of: che.eclipse.org
    app.kubernetes.io/component: workspaces-namespace
  annotations:
    che.eclipse.org/username: $USER_NAME
EOF

oc adm policy add-role-to-user admin $USER_NAME -n $NAMESPACE

echo "Waiting for pipeline serviceaccount in $NAMESPACE..."
until oc get serviceaccounts -n "$NAMESPACE" 2>/dev/null | grep -q pipeline; do
    sleep 10
done

oc adm policy add-cluster-role-to-user pipelines-access-role "system:serviceaccount:$NAMESPACE:pipeline" -n $NAMESPACE
oc adm policy add-cluster-role-to-user jumpstarter-access-role "system:serviceaccount:$NAMESPACE:pipeline" -n $NAMESPACE
#oc adm policy add-cluster-role-to-user system:image-puller "system:serviceaccount:$NAMESPACE:pipeline" -n $NAMESPACE

