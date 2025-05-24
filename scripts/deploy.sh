#!/bin/bash

# Exit on error
set -e

# Load environment variables
source .env

# Build and push Docker image
echo "Building and pushing Docker image..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
docker build -t moikai .
docker tag moikai:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/moikai:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/moikai:latest

# Update ECS service
echo "Updating ECS service..."
aws ecs update-service --cluster moikai-cluster --service moikai-service --force-new-deployment

echo "Deployment completed successfully!" 