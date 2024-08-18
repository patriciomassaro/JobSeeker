#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Function to build and push an image using Cloud Build
build_and_push() {
  local image_name=$1
  local context_path=$2
  local tag=${3:-latest}

  echo "Building $image_name using Cloud Build..."
  gcloud builds submit $context_path --tag gcr.io/$PROJECT_ID/$image_name:$tag

  echo "$image_name has been built and pushed to GCR."
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

# Build and push backend image
build_and_push "backend" "./backend"

# Build and push frontend image
build_and_push "frontend" "./frontend"

echo "All images have been built and pushed to GCR using Cloud Build."
