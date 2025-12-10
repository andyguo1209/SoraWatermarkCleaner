# Deploy to Google Cloud Platform (Cloud Run)

This guide details how to deploy the Sora Watermark Cleaner application to Google Cloud Run.

## Prerequisites

1.  **Google Cloud SDK**: Ensure `gcloud` CLI is installed and authenticated.
2.  **Docker**: Installed locally for building the image (or use Cloud Build).
3.  **GCP Project**: A Google Cloud project with billing enabled.

## 1. Setup Environment Variables

Set your project ID and region:

```bash
export PROJECT_ID="your-project-id"
export REGION="us-central1"
export IMAGE_NAME="sora-cleaner"
export REPO_NAME="sora-repo" # Artifact Registry repository name
```

## 2. Enable Required APIs

```bash
gcloud services enable artifactregistry.googleapis.com run.googleapis.com
```

## 3. Create Artifact Registry Repository

Create a Docker repository in Artifact Registry if you haven't already:

```bash
gcloud artifacts repositories create $REPO_NAME \
    --repository-format=docker \
    --location=$REGION \
    --description="Docker repository for Sora Watermark Cleaner"
```

## 4. Build and Push Docker Image

**Option A: Build locally and push (requires Docker)**

```bash
# Configure Docker to authenticate with Artifact Registry
gcloud auth configure-docker ${REGION}-docker.pkg.dev

# Build the image
docker build --platform linux/amd64 -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest .

# Push the image
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest
```

**Option B: Cloud Build (No local Docker needed)**

```bash
gcloud builds submit --tag ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest .
```

## 5. Deploy to Cloud Run

Deploy the container to Cloud Run. Since we are using SQLite, data will **RESET** on every restart unless we mount a volume. Cloud Run now supports volume mounts (Network File System or Cloud Storage FUSE), but for simplicity, this guide assumes ephemeral storage or that you will configure a volume later if persistence is needed.

**Note on Persistence**: SQLite is a file-based database. Cloud Run instances are ephemeral. If you need persistent user data, consider using Cloud SQL (MySQL/PostgreSQL) or mounting a Cloud Storage bucket as a volume. Since you specifically requested moving to SQLite, be aware of this limitation in a serverless environment.

```bash
gcloud run deploy sora-cleaner \
    --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --port 8501 \
    --memory 2Gi \
    --cpu 2
```

- `--port 8501`: Exposes the Streamlit port.
- `--allow-unauthenticated`: Makes the service publicly accessible. Remove this flag if you want private access.

## 6. Access the Application

After deployment, the command will output a Service URL (e.g., `https://sora-cleaner-xyz.a.run.app`). Open this URL in your browser.
