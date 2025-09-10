# FFmpeg Randomizer Windows Service Setup
# Run this script as Administrator after running setup-environment.ps1

param(
    [string]$AppPath = "C:\apps\ffmpeg-randomizer",
    [string]$ServiceName = "FFmpegRandomizerAPI",
    [string]$NSSMPath = "C:\nssm\nssm.exe"
)

Write-Host "=== FFmpeg Randomizer Service Setup ===" -ForegroundColor Green

# Check if running as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Error "This script must be run as Administrator. Exiting."
    exit 1
}

# Check if NSSM exists
if (!(Test-Path $NSSMPath)) {
    Write-Host "NSSM not found at $NSSMPath" -ForegroundColor Red
    Write-Host "Please download NSSM from https://nssm.cc/download and extract to C:\nssm\" -ForegroundColor Yellow
    Write-Host "Or update the NSSMPath parameter to point to your NSSM installation" -ForegroundColor Yellow
    exit 1
}

# Check if application exists
$uvicornPath = "$AppPath\.venv\Scripts\uvicorn.exe"
if (!(Test-Path $uvicornPath)) {
    Write-Error "Uvicorn not found at $uvicornPath. Please run setup-environment.ps1 first."
    exit 1
}

# Stop existing service if it exists
Write-Host "Checking for existing service..." -ForegroundColor Yellow
$existingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($existingService) {
    Write-Host "Stopping existing service: $ServiceName" -ForegroundColor Yellow
    & $NSSMPath stop $ServiceName
    Start-Sleep -Seconds 3
    
    Write-Host "Removing existing service: $ServiceName" -ForegroundColor Yellow
    & $NSSMPath remove $ServiceName confirm
}

# Install the service
Write-Host "Installing Windows service: $ServiceName" -ForegroundColor Yellow
$arguments = "main:app --host 127.0.0.1 --port 8000"

& $NSSMPath install $ServiceName $uvicornPath $arguments

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install service. NSSM exit code: $LASTEXITCODE"
    exit 1
}

# Configure service settings
Write-Host "Configuring service settings..." -ForegroundColor Yellow

# Set application directory
& $NSSMPath set $ServiceName AppDirectory $AppPath

# Set service description
& $NSSMPath set $ServiceName Description "FFmpeg Randomizer API Server - FastAPI application for media file randomization"

# Set service display name
& $NSSMPath set $ServiceName DisplayName "FFmpeg Randomizer API"

# Configure logging
$logDir = "$AppPath\logs"
if (!(Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force
}

& $NSSMPath set $ServiceName AppStdout "$logDir\service-output.log"
& $NSSMPath set $ServiceName AppStderr "$logDir\service-error.log"

# Set log rotation
& $NSSMPath set $ServiceName AppRotateFiles 1
& $NSSMPath set $ServiceName AppRotateOnline 1
& $NSSMPath set $ServiceName AppRotateSeconds 86400  # Rotate daily
& $NSSMPath set $ServiceName AppRotateBytes 10485760  # 10MB max file size

# Set service startup type to automatic
& $NSSMPath set $ServiceName Start SERVICE_AUTO_START

# Set service recovery options
& $NSSMPath set $ServiceName AppExit Default Restart
& $NSSMPath set $ServiceName AppRestartDelay 5000  # 5 seconds

# Start the service
Write-Host "Starting service: $ServiceName" -ForegroundColor Yellow
& $NSSMPath start $ServiceName

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to start service. NSSM exit code: $LASTEXITCODE"
    Write-Host "Check the service logs at: $logDir" -ForegroundColor Yellow
    exit 1
}

# Wait a moment and check service status
Start-Sleep -Seconds 5
$serviceStatus = & $NSSMPath status $ServiceName

Write-Host "`n=== Service Status ===" -ForegroundColor Green
Write-Host "Service Name: $ServiceName"
Write-Host "Status: $serviceStatus"
Write-Host "Log Directory: $logDir"

# Test the service
Write-Host "`nTesting service..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/" -TimeoutSec 15
    if ($response.StatusCode -eq 200) {
        $content = $response.Content | ConvertFrom-Json
        Write-Host "Service test successful!" -ForegroundColor Green
        Write-Host "API Status: $($content.status)" -ForegroundColor Green
        Write-Host "FFmpeg Available: $($content.ffmpeg_available)" -ForegroundColor Green
    }
} catch {
    Write-Warning "Service test failed: $($_.Exception.Message)"
    Write-Host "Check the service logs for details: $logDir" -ForegroundColor Yellow
}

Write-Host "`n=== Service Management Commands ===" -ForegroundColor Cyan
Write-Host "Start service:   $NSSMPath start $ServiceName"
Write-Host "Stop service:    $NSSMPath stop $ServiceName"
Write-Host "Restart service: $NSSMPath restart $ServiceName"
Write-Host "Service status:  $NSSMPath status $ServiceName"
Write-Host "Remove service:  $NSSMPath remove $ServiceName confirm"

Write-Host "`n=== Next Steps ===" -ForegroundColor Cyan
Write-Host "1. Run setup-caddy.ps1 to configure reverse proxy with HTTPS"
Write-Host "2. Configure your domain's DNS A record"
Write-Host "3. Test your API at https://yourdomain.com/"

Write-Host "`nService setup completed!" -ForegroundColor Green
