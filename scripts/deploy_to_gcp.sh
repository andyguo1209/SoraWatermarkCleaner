#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}== Sora Watermark Cleaner GCP Deployment Script ==${NC}"

# Check for gcloud
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI not found.${NC}"
    echo "Please install Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Load variables (can be set via env vars or interactive prompt)
read_var() {
    local var_name="$1"
    local prompt="$2"
    local default="$3"
    local current_value="${!var_name}"

    if [ -z "$current_value" ]; then
        if [ -n "$default" ]; then
            read -p "$prompt [$default]: " input
            export $var_name="${input:-$default}"
        else
            read -p "$prompt: " input
            export $var_name="$input"
        fi
    fi
}

echo -e "\n${YELLOW}Configuring Deployment Variables...${NC}"
# Attempt to get default project from gcloud config
DEFAULT_PROJECT=$(gcloud config get-value project 2>/dev/null)

read_var "PROJECT_ID" "Enter GCP Project ID" "$DEFAULT_PROJECT"
read_var "REGION" "Enter Region" "us-central1"
read_var "REPO_NAME" "Enter Artifact Registry Repository Name" "sora-repo"
read_var "IMAGE_NAME" "Enter Image Name" "sora-cleaner"
read_var "TAG" "Enter Image Tag" "latest"

FULL_IMAGE_PATH="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:${TAG}"

echo -e "\n${YELLOW}Deployment Configuration:${NC}"
echo "Project ID: $PROJECT_ID"
echo "Region:     $REGION"
echo "Image:      $FULL_IMAGE_PATH"

read -p "Proceed? (y/N) " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

# 0. Check/Create Artifact Registry Repository
echo -e "\n${GREEN}[0/4] Checking Artifact Registry Repository...${NC}"
if ! gcloud artifacts repositories describe "$REPO_NAME" --location="$REGION" &>/dev/null; then
    echo "Repository '$REPO_NAME' not found. Creating..."
    gcloud artifacts repositories create "$REPO_NAME" \
        --repository-format=docker \
        --location="$REGION" \
        --description="Docker repository for Sora Watermark Cleaner"
    echo "Repository created successfully."
else
    echo "Repository '$REPO_NAME' exists."
fi

# 1. Authenticate Docker
echo -e "\n${GREEN}[1/4] Authenticating Docker with Artifact Registry...${NC}"
gcloud auth configure-docker ${REGION}-docker.pkg.dev

# 2. Build Image
echo -e "\n${GREEN}[2/4] Building Docker Image (amd64)...${NC}"
# Use --platform linux/amd64 for compatibility with Cloud Run
docker build --platform linux/amd64 -t "$FULL_IMAGE_PATH" .

# 3. Push Image
echo -e "\n${GREEN}[3/4] Pushing Image to Artifact Registry...${NC}"
docker push "$FULL_IMAGE_PATH"

# 4. Deploy to Cloud Run
echo -e "\n${GREEN}[4/4] Deploying to Cloud Run...${NC}"
echo "Deploying service '${IMAGE_NAME}'..."
gcloud run deploy "$IMAGE_NAME" \
    --image "$FULL_IMAGE_PATH" \
    --region "$REGION" \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 2Gi \
    --cpu 2

echo -e "\n${GREEN}Deployment Complete!${NC}"
