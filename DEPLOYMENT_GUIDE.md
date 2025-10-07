# Cloud Run Video Processing Service - Deployment Guide

This guide provides step-by-step instructions for deploying the video processing service to Google Cloud Run.

## 📋 Prerequisites

Before starting the deployment, ensure you have:

1. **Google Cloud Project** with billing enabled
2. **Google Cloud CLI** installed and authenticated
3. **Docker** installed (for local testing)
4. **Required APIs** enabled in your GCP project:
   - Cloud Run API
   - Cloud Build API
   - Cloud Storage API
   - Cloud Logging API
   - Cloud Monitoring API

## 🚀 Quick Deployment

### Option 1: Automated Deployment (Recommended)

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd ffmpeg-processor

# 2. Set your project ID
export PROJECT_ID=your-gcp-project-id

# 3. Run the deployment script
chmod +x deploy.sh
./deploy.sh
```

### Option 2: Manual Deployment

Follow the manual steps below for more control over the deployment process.

## 🔧 Manual Deployment Steps

### Step 1: Setup Google Cloud Project

```bash
# Set your project ID
export PROJECT_ID=your-gcp-project-id
export REGION=us-central1

# Authenticate with Google Cloud
gcloud auth login
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    storage.googleapis.com \
    logging.googleapis.com \
    monitoring.googleapis.com
```

### Step 2: Create Cloud Storage Bucket

```bash
# Create the storage bucket
gsutil mb -p $PROJECT_ID -l $REGION gs://bg-video-storage

# Create folder structure
echo "Folder structure setup" | gsutil cp - gs://bg-video-storage/raw-video-clips/.keep
echo "Folder structure setup" | gsutil cp - gs://bg-video-storage/processed-video-clips/.keep
echo "Folder structure setup" | gsutil cp - gs://bg-video-storage/temp-service-folder/.keep

# Set bucket permissions (optional - for public access)
gsutil iam ch allUsers:objectViewer gs://bg-video-storage
```

### Step 3: Create Service Account

```bash
# Create service account
gcloud iam service-accounts create video-processor \
    --display-name="Video Processor Service Account" \
    --description="Service account for video processing Cloud Run service"

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:video-processor@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:video-processor@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/logging.logWriter"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:video-processor@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/monitoring.metricWriter"
```

### Step 4: Build and Deploy with Cloud Build

```bash
# Submit build to Cloud Build
gcloud builds submit \
    --config cloudbuild.yaml \
    --substitutions _REGION=$REGION,_BUCKET_NAME=bg-video-storage
```

### Step 5: Configure Cloud Run Service

```bash
# Update service configuration (if needed)
gcloud run services update ffmpeg-video-processor \
    --region=$REGION \
    --memory=4Gi \
    --cpu=2 \
    --timeout=3600 \
    --concurrency=10 \
    --max-instances=5 \
    --set-env-vars="GCS_BUCKET_NAME=bg-video-storage,GCP_PROJECT_ID=$PROJECT_ID"
```

## 🧪 Testing the Deployment

### 1. Get Service URL

```bash
SERVICE_URL=$(gcloud run services describe ffmpeg-video-processor \
    --region=$REGION \
    --format="value(status.url)")

echo "Service URL: $SERVICE_URL"
```

### 2. Test Health Endpoint

```bash
curl -f "$SERVICE_URL/health"
```

### 3. Test Video Listing

```bash
curl "$SERVICE_URL/videos/list"
```

### 4. Test Video Processing

First, upload a test video to the raw-video-clips folder:

```bash
# Upload a test video
gsutil cp your-test-video.mp4 gs://bg-video-storage/raw-video-clips/

# Process the video
curl -X POST "$SERVICE_URL/videos/process" \
    -H "Content-Type: application/json" \
    -d '{
        "video_filename": "your-test-video.mp4",
        "preset": "mobile_vertical"
    }'
```

## 🔧 Configuration Options

### Environment Variables

You can customize the service behavior using environment variables:

```bash
gcloud run services update ffmpeg-video-processor \
    --region=$REGION \
    --set-env-vars="
        GCS_BUCKET_NAME=bg-video-storage,
        GCP_PROJECT_ID=$PROJECT_ID,
        MAX_CONCURRENT_JOBS=3,
        MAX_WORKERS_PER_JOB=2,
        LOG_LEVEL=INFO,
        ENVIRONMENT=production
    "
```

### Resource Configuration

Adjust resources based on your needs:

```bash
# For high-performance processing
gcloud run services update ffmpeg-video-processor \
    --region=$REGION \
    --memory=8Gi \
    --cpu=4 \
    --max-instances=10

# For cost optimization
gcloud run services update ffmpeg-video-processor \
    --region=$REGION \
    --memory=2Gi \
    --cpu=1 \
    --max-instances=3
```

## 📊 Monitoring and Logging

### View Logs

```bash
# View recent logs
gcloud logs read --service=ffmpeg-video-processor --limit=50

# Stream logs in real-time
gcloud logs tail --service=ffmpeg-video-processor

# Filter logs by severity
gcloud logs read --service=ffmpeg-video-processor --filter="severity>=ERROR"
```

### Monitor Performance

```bash
# Check service metrics
gcloud run services describe ffmpeg-video-processor --region=$REGION

# View Cloud Monitoring dashboard
echo "https://console.cloud.google.com/monitoring/dashboards?project=$PROJECT_ID"
```

## 🔒 Security Considerations

### 1. Service Account Permissions

Ensure the service account has minimal required permissions:

```bash
# Review current permissions
gcloud projects get-iam-policy $PROJECT_ID \
    --flatten="bindings[].members" \
    --filter="bindings.members:video-processor@$PROJECT_ID.iam.gserviceaccount.com"
```

### 2. Network Security

For enhanced security, consider using VPC connectors:

```bash
# Create VPC connector (optional)
gcloud compute networks vpc-access connectors create video-processor-connector \
    --region=$REGION \
    --subnet=default \
    --subnet-project=$PROJECT_ID \
    --min-instances=2 \
    --max-instances=10

# Update service to use VPC connector
gcloud run services update ffmpeg-video-processor \
    --region=$REGION \
    --vpc-connector=video-processor-connector \
    --vpc-egress=private-ranges-only
```

### 3. Access Control

Configure IAM for API access:

```bash
# Allow specific users to invoke the service
gcloud run services add-iam-policy-binding ffmpeg-video-processor \
    --region=$REGION \
    --member="user:user@example.com" \
    --role="roles/run.invoker"

# Or allow all authenticated users
gcloud run services add-iam-policy-binding ffmpeg-video-processor \
    --region=$REGION \
    --member="allAuthenticatedUsers" \
    --role="roles/run.invoker"
```

## 🐛 Troubleshooting

### Common Issues

1. **Build Timeout**
   ```bash
   # Increase build timeout
   gcloud config set builds/timeout 1800
   ```

2. **Memory Issues**
   ```bash
   # Increase memory allocation
   gcloud run services update ffmpeg-video-processor \
       --region=$REGION \
       --memory=8Gi
   ```

3. **Permission Errors**
   ```bash
   # Check service account permissions
   gcloud iam service-accounts get-iam-policy \
       video-processor@$PROJECT_ID.iam.gserviceaccount.com
   ```

4. **Storage Access Issues**
   ```bash
   # Test bucket access
   gsutil ls gs://bg-video-storage/
   ```

### Debug Commands

```bash
# Get service details
gcloud run services describe ffmpeg-video-processor --region=$REGION

# Check recent revisions
gcloud run revisions list --service=ffmpeg-video-processor --region=$REGION

# View build history
gcloud builds list --limit=10

# Test local container
docker run -p 8080:8080 gcr.io/$PROJECT_ID/ffmpeg-video-processor:latest
```

## 🔄 Updates and Maintenance

### Deploy Updates

```bash
# Rebuild and deploy
gcloud builds submit --config cloudbuild.yaml

# Deploy specific image
gcloud run deploy ffmpeg-video-processor \
    --image=gcr.io/$PROJECT_ID/ffmpeg-video-processor:latest \
    --region=$REGION
```

### Cleanup Old Resources

```bash
# Clean up old container images
gcloud container images list-tags gcr.io/$PROJECT_ID/ffmpeg-video-processor \
    --limit=999999 --sort-by=TIMESTAMP \
    --filter="timestamp.datetime < '$(date -d '30 days ago' --iso-8601)'" \
    --format="get(digest)" | xargs -I {} gcloud container images delete gcr.io/$PROJECT_ID/ffmpeg-video-processor@{}

# Clean up old Cloud Build logs
gcloud logging sinks create build-logs-cleanup \
    bigquery.googleapis.com/projects/$PROJECT_ID/datasets/build_logs \
    --log-filter='resource.type="build"'
```

## 📞 Support

For issues and support:

1. Check the [troubleshooting section](#troubleshooting)
2. Review Cloud Run documentation
3. Check Cloud Build logs for build issues
4. Monitor Cloud Logging for runtime issues

## 🎉 Success!

Your video processing service should now be running on Cloud Run. You can:

- Process videos via the REST API
- Monitor performance through Cloud Monitoring
- Scale automatically based on demand
- Access logs through Cloud Logging

The service URL will be: `https://ffmpeg-video-processor-[hash]-[region].a.run.app`
