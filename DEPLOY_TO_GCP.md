# Deploy to Google Cloud Platform (Cloud Run)

This guide details how to deploy the Sora Watermark Cleaner application to Google Cloud Run.

## Prerequisites

1.  **Google Cloud SDK**: Ensure `gcloud` CLI is installed and authenticated.
2.  **Docker**: Installed locally for building the image (or use Cloud Build).
3.  **GCP Project**: A Google Cloud project with billing enabled.

## 1. Fast Deployment (Recommended)

We have provided a script to automate the build, push, and deploy process.

```bash
./scripts/deploy_to_gcp.sh
```

Follow the interactive prompts to enter your Project ID and Region.

---

## 2. Manual Deployment Steps

If you prefer to run commands manually:

### Setup Environment

```bash
export PROJECT_ID="your-project-id"
export REGION="us-central1"
export IMAGE_NAME="sora-cleaner"
export REPO_NAME="sora-repo"
```

### Create Repository (One-time)

```bash
gcloud artifacts repositories create $REPO_NAME \
    --repository-format=docker \
    --location=$REGION \
    --description="Docker repository for Sora Watermark Cleaner"
```

### Build and Push

```bash
gcloud auth configure-docker ${REGION}-docker.pkg.dev

# IMPORTANT: Build for linux/amd64
docker build --platform linux/amd64 -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest .

docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest
```

### Deploy to Cloud Run

**Note**: We now expose port **8080** (Nginx), which handles both the frontend and API.

```bash
gcloud run deploy sora-cleaner \
    --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 2Gi \
    --cpu 2
```

## 3. Access the Application

After deployment, Cloud Run will provide a URL (e.g., `https://sora-cleaner-xyz.a.run.app`).
- **UI**: Visit the root URL.
- **API**: Visit `/api/docs` on the same URL.
