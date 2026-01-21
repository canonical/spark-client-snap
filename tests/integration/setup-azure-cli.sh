#!/bin/bash

if ! command -v az >/dev/null 2>&1
then
    cat << EOF
'az' command could not be found.
Please install az using either:
- pipx install azure-cli
- uv tool install azure-cli --prerelease=allow
- snap install azcli
  snap alias azcli az
EOF

    exit 1
fi


# Early check to see if the two required environment variables are set.
if [[ -z "${AZURE_STORAGE_ACCOUNT}" || -z "${AZURE_STORAGE_KEY}" ]]; then
  echo "Error: AZURE_STORAGE_ACCOUNT and/or AZURE_STORAGE_KEY variable is not set."
  exit 1
fi
echo "The variables AZURE_STORAGE_ACCOUNT and AZURE_STORAGE_KEY are found to be set."


# Test if the credentials are correct by listing containers
echo "Testing Azure Storage credentials..."
if ! az storage container list > /dev/null 2>&1; then
  echo "Error: Invalid Azure Storage credentials."
  exit 1
fi

echo "Azure CLI setup successfully."