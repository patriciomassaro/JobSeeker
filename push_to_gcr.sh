#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Function to build and push an image
build_and_push() {
  local image_name=$1
  local dockerfile_path=$2
  local tag=${3:-latest}

  echo "Building $image_name..."
  docker build $image_name -t $image_name:$tag

  echo "Tagging $image_name..."
  docker tag $image_name:$tag gcr.io/$PROJECT_ID/$image_name:$tag

  echo "Pushing $image_name to GCR..."
  docker push gcr.io/$PROJECT_ID/$image_name:$tag

  echo "$image_name has been pushed to GCR."
}

# Check if PROJECT_ID is set
if [ -z "$PROJECT_ID" ]; then
  echo "ERROR: PROJECT_ID is not set. Please set it with: export PROJECT_ID=your-project-id"
  exit 1
fi

# Authenticate with Google Cloud (if not already authenticated)
if ! gcloud auth print-access-token &>/dev/null; then
  echo "Authenticating with Google Cloud..."
  gcloud auth login
fi

# Configure Docker to use gcloud as a credential helper
gcloud auth configure-docker

# Build and push backend image
build_and_push "backend" "./backend/Dockerfile"

# Build and push frontend image
build_and_push "frontend" "./frontend/Dockerfile"

echo "All images have been built and pushed to GCR."
