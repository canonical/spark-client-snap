#!/bin/bash

CURRENT_UID=$(id -u)
CURRENT_GID=$(id -g)
CURRENT_USER=$(id -un 2>/dev/null || echo "sparkuser")

# Clean username of special chars (like corporate email @ domains)
CLEAN_USER=$(echo "$CURRENT_USER" | tr -cd '[:alnum:]_.-')

# Create a private, unique mock directory inside the Snap's /tmp sandbox layout
MOCK_DIR="/tmp/spark-user-mock-${CURRENT_UID}"
mkdir -p "$MOCK_DIR"

# Generate fake pass-through user entries on the fly
echo "${CLEAN_USER}:x:${CURRENT_UID}:${CURRENT_GID}:Spark Mock User:${MOCK_DIR}:/bin/bash" >"$MOCK_DIR/passwd"
echo "${CLEAN_USER}:x:${CURRENT_GID}:" >"$MOCK_DIR/group"

# Dynamically locate libnss_wrapper.so inside the multi-arch snap structure
NSS_WRAPPER_SO=$(find "$SNAP/usr/lib" -name "libnss_wrapper.so" | head -n 1)

if [ -n "$NSS_WRAPPER_SO" ] && [ -f "$NSS_WRAPPER_SO" ]; then
    export LD_PRELOAD="$NSS_WRAPPER_SO"
    export NSS_WRAPPER_PASSWD="$MOCK_DIR/passwd"
    export NSS_WRAPPER_GROUP="$MOCK_DIR/group"
fi

if [[ ! -n "$KUBECONFIG" ]]; then
    KUBECONFIG="$SNAP_REAL_HOME/.kube/config"
fi

if [[ -n "$PYTHONPATH" ]]; then
    PYTHONPATH="/usr/lib/python310.zip:/usr/lib/python3.10:/usr/lib/python3.10/lib-dynload:$SNAP/lib/python3.10/site-packages:$PYTHONPATH"
fi

KUBECONFIG=$KUBECONFIG exec "$@"
