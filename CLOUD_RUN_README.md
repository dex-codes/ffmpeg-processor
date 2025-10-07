# Video Processing Service for Google Cloud Run

A cloud-native video processing service built for Google Cloud Run that processes videos stored in Google Cloud Storage using FFmpeg. This service provides REST API endpoints for single video processing, batch processing, and video sequence concatenation.

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Client App    │───▶│   Cloud Run      │───▶│  Cloud Storage  │
│                 │    │   FastAPI        │    │                 │
│                 │    │   Service        │    │  bg-video-      │
└─────────────────┘    └──────────────────┘    │  storage        │
                                               │                 │
                                               │ ├─raw-video-    │
                                               │ │ clips/        │
                                               │ ├─processed-    │
                                               │ │ video-clips/  │
                                               │ └─temp-service- │
                                               │   folder/       │
                                               └─────────────────┘
```

## 🚀 Features

- **Single Video Processing**: Process individual videos with customizable presets
- **Batch Processing**: Process multiple videos concurrently
- **Video Sequence**: Concatenate multiple videos into a single output
- **Cloud Storage Integration**: Seamless integration with Google Cloud Storage
- **Async Job Processing**: Background job processing with status tracking
- **Health Monitoring**: Comprehensive health checks and performance monitoring
- **Auto-scaling**: Cloud Run auto-scaling based on demand
- **Structured Logging**: Cloud Logging integration for observability

## 📁 Storage Structure

The service uses the following Google Cloud Storage bucket structure:

```
bg-video-storage/
├── raw-video-clips/          # Source videos for processing
├── processed-video-clips/    # Output processed videos
└── temp-service-folder/      # Temporary files during processing
```

## 🛠️ Quick Start

### Prerequisites

- Google Cloud Project with billing enabled
- Google Cloud CLI (`gcloud`) installed and authenticated
- Docker installed (for local development)
- Python 3.11+ (for local development)
- FFmpeg installed (for local development)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd ffmpeg-processor
chmod +x setup.py deploy.sh
```

### 2. Local Development Setup

```bash
# Setup local development environment
python setup.py

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Update configuration
cp .env.example .env
# Edit .env with your project details
```

### 3. Deploy to Cloud Run

```bash
# Set your project ID
export PROJECT_ID=your-gcp-project-id

# Run deployment script
./deploy.sh
```

## 📚 API Documentation

### Base URL
```
https://your-service-url.run.app
```

### Endpoints

#### Health Check
```http
GET /health
```
Returns service health status and system metrics.

#### List Available Videos
```http
GET /videos/list?prefix=&limit=100
```
List raw videos available for processing.

#### Process Single Video
```http
POST /videos/process
Content-Type: application/json

{
  "video_filename": "example.mp4",
  "preset": "mobile_vertical",
  "custom_settings": {
    "frame_width": 1080,
    "frame_height": 1920
  }
}
```

#### Process Video Batch
```http
POST /videos/batch
Content-Type: application/json

{
  "video_filenames": ["video1.mp4", "video2.mp4"],
  "preset": "youtube_shorts",
  "max_concurrent": 2
}
```

#### Process Video Sequence
```http
POST /videos/sequence
Content-Type: application/json

{
  "video_filenames": ["intro.mp4", "main.mp4", "outro.mp4"],
  "output_filename": "final_sequence.mp4",
  "preset": "mobile_vertical"
}
```

#### Get Available Presets
```http
GET /presets
```
Returns available video processing presets.

#### Get Processing Statistics
```http
GET /stats
```
Returns processing statistics and metrics.

## 🎛️ Video Presets

The service includes predefined presets for common video formats:

- **mobile_vertical**: 1080x1920, 30fps (TikTok, Instagram Stories)
- **youtube_shorts**: 1080x1920, 30fps, 8M bitrate
- **youtube_standard**: 1920x1080, 30fps, 8M bitrate
- **instagram_post**: 1080x1080, 30fps (Square format)
- **high_quality**: 1080x1920, 60fps, 12M bitrate
- **low_bandwidth**: 720x1280, 24fps, 2M bitrate

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GCS_BUCKET_NAME` | Cloud Storage bucket name | `bg-video-storage` |
| `GCP_PROJECT_ID` | Google Cloud Project ID | Auto-detected |
| `MAX_CONCURRENT_JOBS` | Maximum concurrent processing jobs | `3` |
| `MAX_WORKERS_PER_JOB` | FFmpeg workers per job | `2` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `ENVIRONMENT` | Deployment environment | `production` |

### Custom Processing Settings

You can override preset settings by providing custom settings:

```json
{
  "frame_width": 1920,
  "frame_height": 1080,
  "frame_rate": 60,
  "bitrate": "10M"
}
```

## 🧪 Testing

### Run Local Tests
```bash
# Activate virtual environment
source venv/bin/activate

# Run tests
pytest tests/

# Run with coverage
pytest --cov=. tests/
```

### Test API Endpoints
```bash
# Test health endpoint
curl https://your-service-url.run.app/health

# Test video listing
curl https://your-service-url.run.app/videos/list

# Test video processing
curl -X POST https://your-service-url.run.app/videos/process \
  -H "Content-Type: application/json" \
  -d '{"video_filename": "test.mp4", "preset": "mobile_vertical"}'
```

## 📊 Monitoring

The service includes comprehensive monitoring:

- **Health Checks**: `/health` endpoint with system metrics
- **Performance Monitoring**: CPU, memory, disk usage tracking
- **Job Tracking**: Processing statistics and error rates
- **Cloud Logging**: Structured logs in Google Cloud Logging
- **Error Tracking**: Automatic error reporting and alerting

## 🔒 Security

- **Service Account**: Dedicated service account with minimal permissions
- **IAM Roles**: Least privilege access to Cloud Storage
- **CORS Configuration**: Configurable CORS policies
- **Input Validation**: Request validation using Pydantic models
- **Error Handling**: Secure error responses without sensitive data

## 🚀 Deployment Options

### Cloud Build (Recommended)
```bash
gcloud builds submit --config cloudbuild.yaml
```

### Manual Docker Build
```bash
docker build -t gcr.io/$PROJECT_ID/ffmpeg-video-processor .
docker push gcr.io/$PROJECT_ID/ffmpeg-video-processor
gcloud run deploy --image gcr.io/$PROJECT_ID/ffmpeg-video-processor
```

## 📈 Performance

- **Concurrent Processing**: Up to 5 concurrent video jobs
- **Auto-scaling**: 0-5 instances based on demand
- **Memory**: 4GB per instance
- **CPU**: 2 vCPU per instance
- **Timeout**: 1 hour per request
- **Cold Start**: ~10-15 seconds

## 🐛 Troubleshooting

### Common Issues

1. **FFmpeg not found**
   - Ensure FFmpeg is installed in the container
   - Check Dockerfile for proper FFmpeg installation

2. **GCS permission errors**
   - Verify service account has Storage Object Admin role
   - Check bucket name and project ID configuration

3. **Memory issues**
   - Increase Cloud Run memory allocation
   - Reduce concurrent job limits

4. **Timeout errors**
   - Increase Cloud Run timeout setting
   - Optimize video processing parameters

### Logs and Debugging

```bash
# View Cloud Run logs
gcloud logs read --service=ffmpeg-video-processor

# Stream logs in real-time
gcloud logs tail --service=ffmpeg-video-processor

# Check service status
gcloud run services describe ffmpeg-video-processor --region=us-central1
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review Cloud Run and Cloud Storage documentation
