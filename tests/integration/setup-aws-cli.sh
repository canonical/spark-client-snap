#!/bin/bash

# Install AWS CLI
sudo snap install aws-cli --classic

# Get Access key and secret key from MicroCeph
ACCESS_KEY=foo
SECRET_KEY=bar

get_s3_endpoint() {
    # Get S3 endpoint from Microceph
    ip=$(ip route get 1.1.1.1 | awk '{print $7; exit}')
    echo $ip
}

wait_and_retry() {
    # Retry a command for a number of times by waiting a few seconds.

    command="$@"
    retries=0
    max_retries=50
    until [ "$retries" -ge $max_retries ]; do
        $command &>/dev/null && break
        retries=$((retries + 1))
        echo "Trying to execute command ${command}..."
        sleep 5
    done

    # If the command was not successful even on maximum retries
    if [ "$retries" -ge $max_retries ]; then
        echo "Maximum number of retries ($max_retries) reached. ${command} returned with non zero status."
        exit 1
    fi
}

# Wait for `microceph radosgw` service to be ready and S3 endpoint to be available
wait_and_retry get_s3_endpoint
S3_ENDPOINT=$(get_s3_endpoint)

DEFAULT_REGION="us-east-1"

# Configure AWS CLI credentials
aws configure set aws_access_key_id $ACCESS_KEY
aws configure set aws_secret_access_key $SECRET_KEY
aws configure set default.region $DEFAULT_REGION
aws configure set endpoint_url "http://$S3_ENDPOINT"

wait_and_retry aws --no-verify-ssl s3 ls
echo "AWS CLI credentials set successfully"
