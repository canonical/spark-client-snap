#!/bin/bash

# Install AWS CLI
sudo snap install aws-cli --classic

# Get Access key and secret key from MinIO
ACCESS_KEY=$(kubectl get secret -n minio-operator microk8s-user-1 -o jsonpath='{.data.CONSOLE_ACCESS_KEY}' | base64 -d)
SECRET_KEY=$(kubectl get secret -n minio-operator microk8s-user-1 -o jsonpath='{.data.CONSOLE_SECRET_KEY}' | base64 -d)

get_s3_endpoint(){
    # Get S3 endpoint from MinIO
    kubectl get service minioo -n minio-operator -o jsonpath='{.spec.clusterIP}' 
}

# Wait for `minio` service to be ready and S3 endpoint to be available
retries=0
max_retries=20
until [ "$retries" -ge $max_retries ]
do
    get_s3_endpoint &> /dev/null && break
    retries=$((retries+1)) 
    echo "Waiting for minio service to be up and running..."
    sleep 5
done
if [ "$retries" -ge $max_retries ]; then
    echo "Maximum number of retries ($max_retries) reached. Service 'minio' is not available."
    exit 1
fi

S3_ENDPOINT=$(get_s3_endpoint)

DEFAULT_REGION="us-east-2"

# Configure AWS CLI credentials
aws configure set aws_access_key_id $ACCESS_KEY
aws configure set aws_secret_access_key $SECRET_KEY
aws configure set default.region $DEFAULT_REGION
aws configure set endpoint_url "http://$S3_ENDPOINT"


retries=0
max_retries=20
until [ "$retries" -ge $max_retries ]
do
    aws s3 ls &> /dev/null && break
    retries=$((retries+1)) 
    echo "Waiting for MinIO credentials to be set..."
    sleep 5
done
if [ "$retries" -ge $max_retries ]; then
    echo "Maximum number of retries ($max_retries) reached. AWS CLI credentials could not be set."
    exit 1
fi

echo "AWS CLI credentials set successfully"