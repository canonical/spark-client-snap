#!/bin/bash

# Install AWS CLI
sudo snap install aws-cli --classic

# Get Access key and secret key from MinIO
ACCESS_KEY=$(kubectl get secret -n minio-operator microk8s-user-1 -o jsonpath='{.data.CONSOLE_ACCESS_KEY}' | base64 -d)
SECRET_KEY=$(kubectl get secret -n minio-operator microk8s-user-1 -o jsonpath='{.data.CONSOLE_SECRET_KEY}' | base64 -d)

get_s3_endpoint(){
    # Get S3 endpoint from MinIO
    kubectl get service minio -n minio-operator -o jsonpath='{.spec.clusterIP}' 
}

# Wait for `minio` service to be ready and S3 endpoint to be available
until get_s3_endpoint &> /dev/null ; do
    sleep 5
done

S3_ENDPOINT=$(get_s3_endpoint)

DEFAULT_REGION="us-east-2"

# Configure AWS CLI credentials
aws configure set aws_access_key_id $ACCESS_KEY
aws configure set aws_secret_access_key $SECRET_KEY
aws configure set default.region $DEFAULT_REGION
aws configure set endpoint_url "http://$S3_ENDPOINT"
echo "AWS CLI credentials set successfully"