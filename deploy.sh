#!/bin/bash

# Cloud Run Deployment Script for Video Processing Service
# This script automates the deployment of the video processing service to Google Cloud Run

set -e  # Exit on any error

# Configuration
PROJECT_ID="${PROJECT_ID:-}"
REGION="${REGION:-us-central1}"
SERVICE_NAME="${SERVICE_NAME:-ffmpeg-video-processor}"
BUCKET_NAME="${BUCKET_NAME:-bg-video-storage}"
SERVICE_ACCOUNT="${SERVICE_ACCOUNT:-video-processor@${PROJECT_ID}.iam.gserviceaccount.com}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install it first."
        exit 1
    fi
    
    # Check if PROJECT_ID is set
    if [ -z "$PROJECT_ID" ]; then
        log_error "PROJECT_ID environment variable is not set."
        echo "Please set it with: export PROJECT_ID=your-project-id"
        exit 1
    fi
    
    # Check if authenticated with gcloud
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        log_error "Not authenticated with gcloud. Please run: gcloud auth login"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Setup GCP project and services
setup_gcp() {
    log_info "Setting up GCP project and enabling required services..."
    
    # Set the project
    gcloud config set project $PROJECT_ID
    
    # Enable required APIs
    log_info "Enabling required APIs..."
    gcloud services enable \
        cloudbuild.googleapis.com \
        run.googleapis.com \
        storage.googleapis.com \
        logging.googleapis.com \
        monitoring.googleapis.com
    
    log_success "GCP setup completed"
}

# Create storage bucket if it doesn't exist
setup_storage() {
    log_info "Setting up Cloud Storage bucket..."
    
    # Check if bucket exists
    if gsutil ls -b gs://$BUCKET_NAME &> /dev/null; then
        log_info "Bucket gs://$BUCKET_NAME already exists"
    else
        log_info "Creating bucket gs://$BUCKET_NAME..."
        gsutil mb -p $PROJECT_ID -l $REGION gs://$BUCKET_NAME
        log_success "Bucket created"
    fi
    
    # Create folder structure
    log_info "Setting up folder structure..."
    echo "Folder structure setup" | gsutil cp - gs://$BUCKET_NAME/raw-video-clips/.keep
    echo "Folder structure setup" | gsutil cp - gs://$BUCKET_NAME/processed-video-clips/.keep
    echo "Folder structure setup" | gsutil cp - gs://$BUCKET_NAME/temp-service-folder/.keep
    
    log_success "Storage setup completed"
}

# Create service account and set permissions
setup_service_account() {
    log_info "Setting up service account..."
    
    SA_NAME="video-processor"
    SA_EMAIL="$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"
    
    # Check if service account exists
    if gcloud iam service-accounts describe $SA_EMAIL &> /dev/null; then
        log_info "Service account $SA_EMAIL already exists"
    else
        log_info "Creating service account..."
        gcloud iam service-accounts create $SA_NAME \
            --display-name="Video Processor Service Account" \
            --description="Service account for video processing Cloud Run service"
        log_success "Service account created"
    fi
    
    # Grant necessary permissions
    log_info "Granting permissions to service account..."
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SA_EMAIL" \
        --role="roles/storage.objectAdmin"
    
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SA_EMAIL" \
        --role="roles/logging.logWriter"
    
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SA_EMAIL" \
        --role="roles/monitoring.metricWriter"
    
    log_success "Service account setup completed"
}

# Build and deploy using Cloud Build
deploy_service() {
    log_info "Building and deploying service using Cloud Build..."
    
    # Submit build
    gcloud builds submit \
        --config cloudbuild.yaml \
        --substitutions _REGION=$REGION,_BUCKET_NAME=$BUCKET_NAME,_SERVICE_ACCOUNT=$SERVICE_ACCOUNT \
        .
    
    log_success "Service deployed successfully"
}

# Test the deployment
test_deployment() {
    log_info "Testing deployment..."
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
        --region=$REGION \
        --format="value(status.url)")
    
    if [ -z "$SERVICE_URL" ]; then
        log_error "Failed to get service URL"
        return 1
    fi
    
    log_info "Service URL: $SERVICE_URL"
    
    # Test health endpoint
    log_info "Testing health endpoint..."
    if curl -f -s "$SERVICE_URL/health" > /dev/null; then
        log_success "Health check passed"
    else
        log_error "Health check failed"
        return 1
    fi
    
    # Test root endpoint
    log_info "Testing root endpoint..."
    if curl -f -s "$SERVICE_URL/" > /dev/null; then
        log_success "Root endpoint test passed"
    else
        log_error "Root endpoint test failed"
        return 1
    fi
    
    log_success "Deployment tests passed"
    echo ""
    echo "🎉 Deployment completed successfully!"
    echo "Service URL: $SERVICE_URL"
    echo ""
    echo "Available endpoints:"
    echo "  - Health check: $SERVICE_URL/health"
    echo "  - List videos: $SERVICE_URL/videos/list"
    echo "  - Process video: $SERVICE_URL/videos/process"
    echo "  - Process batch: $SERVICE_URL/videos/batch"
    echo "  - Process sequence: $SERVICE_URL/videos/sequence"
    echo "  - Get presets: $SERVICE_URL/presets"
    echo "  - Get stats: $SERVICE_URL/stats"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up temporary files..."
    # Add any cleanup logic here
}

# Main deployment function
main() {
    echo "🚀 Starting Cloud Run deployment for Video Processing Service"
    echo "=================================================="
    echo "Project ID: $PROJECT_ID"
    echo "Region: $REGION"
    echo "Service Name: $SERVICE_NAME"
    echo "Bucket Name: $BUCKET_NAME"
    echo "=================================================="
    echo ""
    
    # Set trap for cleanup
    trap cleanup EXIT
    
    # Run deployment steps
    check_prerequisites
    setup_gcp
    setup_storage
    setup_service_account
    deploy_service
    test_deployment
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --project-id)
            PROJECT_ID="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --service-name)
            SERVICE_NAME="$2"
            shift 2
            ;;
        --bucket-name)
            BUCKET_NAME="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --project-id      GCP Project ID"
            echo "  --region          GCP Region (default: us-central1)"
            echo "  --service-name    Cloud Run service name (default: ffmpeg-video-processor)"
            echo "  --bucket-name     GCS bucket name (default: bg-video-storage)"
            echo "  --help            Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  PROJECT_ID        GCP Project ID (required)"
            echo "  REGION            GCP Region"
            echo "  SERVICE_NAME      Cloud Run service name"
            echo "  BUCKET_NAME       GCS bucket name"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Run main function
main
