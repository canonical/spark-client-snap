#!/bin/bash

if [[ ! -n "$KUBECONFIG" ]]; then
  KUBECONFIG="$SNAP_REAL_HOME/.kube/config"
fi

if [[ -n "$PYTHONPATH" ]]; then
  PYTHONPATH="/usr/lib/python310.zip:/usr/lib/python3.10:/usr/lib/python3.10/lib-dynload:$SNAP/lib/python3.10/site-packages:$PYTHONPATH"
fi

KUBECONFIG=$KUBECONFIG exec "$@"
