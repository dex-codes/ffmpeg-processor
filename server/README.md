# FFmpeg Randomizer Server

A FastAPI-based server for randomizing video and audio files using FFmpeg.

## Features

- Upload media files for randomization
- Multiple randomization effects (basic, glitch, audio-focused)
- Configurable effect intensity
- RESTful API with automatic documentation
- Health check endpoints
- File download functionality

## Prerequisites

- Python 3.8+
- FFmpeg installed and available in PATH
- Windows Server/VPS (for deployment guide)

## Local Development Setup

1. **Create virtual environment:**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

3. **Install FFmpeg:**
   - Download FFmpeg from https://ffmpeg.org/download.html
   - Add FFmpeg to your system PATH
   - Verify installation: `ffmpeg -version`

4. **Run the server:**
   ```powershell
   uvicorn main:app --host 127.0.0.1 --port 8000 --reload
   ```

5. **Access the API:**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## API Endpoints

### GET /
Health check endpoint

### GET /health
Detailed health check with system status

### POST /randomize
Upload and randomize a media file
- **file**: Media file (multipart/form-data)
- **effect_type**: "basic", "glitch", or "audio" (optional, default: "basic")
- **intensity**: Float between 0.0 and 1.0 (optional, default: 0.5)

### GET /effects
List available randomization effects

### GET /download/{filename}
Download a processed file

## Production Deployment (Windows VPS)

Follow the deployment guide in your documentation for setting up with Caddy and Windows Services.

## Directory Structure

```
server/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── README.md           # This file
├── uploads/            # Temporary upload directory
├── outputs/            # Processed files directory
└── temp/               # Temporary processing files
```

## Configuration

The application creates the following directories automatically:
- `uploads/` - Temporary storage for uploaded files
- `outputs/` - Storage for processed files
- `temp/` - Temporary processing files

## Error Handling

The API includes comprehensive error handling for:
- Missing FFmpeg installation
- File processing errors
- Timeout handling (5-minute limit)
- Invalid file formats
- Missing files

## Security Notes

For production deployment:
- Configure CORS origins properly
- Implement authentication if needed
- Set up proper file cleanup routines
- Configure firewall rules
- Use HTTPS (handled by Caddy in deployment guide)
