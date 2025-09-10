# FFmpeg Randomizer Server - Windows VPS Deployment Guide

This guide will help you deploy the FFmpeg Randomizer API on a Windows VPS with automatic HTTPS using Caddy.

## Prerequisites

1. **Windows Server/VPS** with Administrator access
2. **Domain name** pointing to your VPS IP address (A record)
3. **Python 3.8+** installed
4. **FFmpeg** installed and in PATH
5. **PowerShell** (comes with Windows)

## Quick Deployment

### Step 1: Prepare Your VPS

1. **Point your domain to your VPS:**
   - Create an A record: `api.yourdomain.com` → `YOUR_VPS_IP`
   - Wait for DNS propagation (can take up to 24 hours)

2. **Open PowerShell as Administrator**

### Step 2: Run Automated Setup

1. **Download and extract your application files** to your VPS
2. **Navigate to the application directory:**
   ```powershell
   cd "path\to\your\ffmpeg-randomizer\server"
   ```

3. **Run the environment setup:**
   ```powershell
   .\setup-environment.ps1 -Domain "api.yourdomain.com"
   ```

4. **Download NSSM (Non-Sucking Service Manager):**
   - Download from: https://nssm.cc/download
   - Extract `nssm.exe` to `C:\nssm\nssm.exe`

5. **Setup the API service:**
   ```powershell
   .\setup-service.ps1
   ```

6. **Download Caddy:**
   - Download from: https://caddyserver.com/download
   - Place `caddy.exe` in `C:\caddy\caddy.exe`

7. **Setup Caddy reverse proxy:**
   ```powershell
   .\setup-caddy.ps1 -Domain "api.yourdomain.com"
   ```

### Step 3: Verify Deployment

1. **Check services are running:**
   ```powershell
   Get-Service FFmpegRandomizerAPI, Caddy
   ```

2. **Test your API:**
   - Visit: `https://api.yourdomain.com/`
   - API docs: `https://api.yourdomain.com/docs`

## Manual Deployment Steps

If you prefer to set up manually or need to troubleshoot:

### 1. Environment Setup

```powershell
# Create application directory
mkdir C:\apps\ffmpeg-randomizer
cd C:\apps\ffmpeg-randomizer

# Copy your application files
# main.py, requirements.txt, etc.

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

# Create directories
mkdir uploads, outputs, temp, logs
```

### 2. Install FFmpeg

1. Download FFmpeg from https://ffmpeg.org/download.html
2. Extract and add to system PATH
3. Verify: `ffmpeg -version`

### 3. Setup Windows Service

```powershell
# Install NSSM service
C:\nssm\nssm.exe install FFmpegRandomizerAPI `
  "C:\apps\ffmpeg-randomizer\.venv\Scripts\uvicorn.exe" `
  "main:app --host 127.0.0.1 --port 8000"

# Configure service
C:\nssm\nssm.exe set FFmpegRandomizerAPI AppDirectory "C:\apps\ffmpeg-randomizer"
C:\nssm\nssm.exe set FFmpegRandomizerAPI Description "FFmpeg Randomizer API Server"

# Start service
C:\nssm\nssm.exe start FFmpegRandomizerAPI
```

### 4. Setup Caddy

```powershell
# Create Caddy directory
mkdir C:\caddy
cd C:\caddy

# Create Caddyfile
@"
api.yourdomain.com {
    encode gzip
    reverse_proxy 127.0.0.1:8000
}
"@ | Out-File -FilePath Caddyfile -Encoding UTF8

# Install Caddy service
C:\nssm\nssm.exe install Caddy "C:\caddy\caddy.exe" "run --config C:\caddy\Caddyfile"
C:\nssm\nssm.exe start Caddy
```

### 5. Configure Firewall

```powershell
New-NetFirewallRule -DisplayName "HTTP Inbound" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 80
New-NetFirewallRule -DisplayName "HTTPS Inbound" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 443
```

## Service Management

### Start/Stop Services

```powershell
# FFmpeg Randomizer API
C:\nssm\nssm.exe start FFmpegRandomizerAPI
C:\nssm\nssm.exe stop FFmpegRandomizerAPI
C:\nssm\nssm.exe restart FFmpegRandomizerAPI

# Caddy
C:\nssm\nssm.exe start Caddy
C:\nssm\nssm.exe stop Caddy
C:\nssm\nssm.exe restart Caddy
```

### Check Service Status

```powershell
C:\nssm\nssm.exe status FFmpegRandomizerAPI
C:\nssm\nssm.exe status Caddy
```

### View Logs

- **API Logs:** `C:\apps\ffmpeg-randomizer\logs\`
- **Caddy Logs:** `C:\caddy\logs\`

## Updating Your Application

1. **Stop the API service:**
   ```powershell
   C:\nssm\nssm.exe stop FFmpegRandomizerAPI
   ```

2. **Update your code:**
   ```powershell
   cd C:\apps\ffmpeg-randomizer
   # Copy new files, update dependencies, etc.
   .\.venv\Scripts\pip install -r requirements.txt
   ```

3. **Start the service:**
   ```powershell
   C:\nssm\nssm.exe start FFmpegRandomizerAPI
   ```

## Troubleshooting

### Common Issues

1. **Service won't start:**
   - Check logs in `C:\apps\ffmpeg-randomizer\logs\`
   - Verify Python virtual environment is working
   - Ensure FFmpeg is in PATH

2. **HTTPS not working:**
   - Verify DNS A record is correct
   - Check Caddy logs in `C:\caddy\logs\`
   - Ensure ports 80 and 443 are open

3. **API returns errors:**
   - Check FFmpeg installation: `ffmpeg -version`
   - Verify file permissions on upload/output directories
   - Check API logs for specific error messages

### Log Locations

- **API Service:** `C:\apps\ffmpeg-randomizer\logs\service-*.log`
- **Caddy:** `C:\caddy\logs\*.log`
- **Windows Event Log:** Check Windows Event Viewer for service errors

## Security Considerations

1. **Firewall:** Only open ports 80 and 443
2. **File Cleanup:** Implement regular cleanup of upload/output directories
3. **Rate Limiting:** Configure rate limiting in Caddy if needed
4. **Authentication:** Add API authentication for production use
5. **CORS:** Configure CORS origins properly in `main.py`

## Performance Tuning

1. **Worker Processes:** Consider using Gunicorn with multiple workers for high load
2. **File Storage:** Use separate disk/partition for uploads/outputs
3. **Memory:** Monitor memory usage during FFmpeg processing
4. **Cleanup:** Implement automatic cleanup of old files

## Support

For issues with:
- **FastAPI:** Check the FastAPI documentation
- **Caddy:** Check Caddy documentation and logs
- **NSSM:** Check NSSM documentation
- **FFmpeg:** Verify FFmpeg installation and PATH configuration
