# FFmpeg Randomizer Server Setup Script
# Run this script as Administrator

param(
    [string]$AppPath = "C:\apps\ffmpeg-randomizer",
    [string]$Domain = "",
    [switch]$SkipFirewall = $false
)

Write-Host "=== FFmpeg Randomizer Server Setup ===" -ForegroundColor Green

# Check if running as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Error "This script must be run as Administrator. Exiting."
    exit 1
}

# Create application directory
Write-Host "Creating application directory: $AppPath" -ForegroundColor Yellow
if (!(Test-Path $AppPath)) {
    New-Item -ItemType Directory -Path $AppPath -Force
}

# Copy application files
Write-Host "Copying application files..." -ForegroundColor Yellow
$currentDir = Get-Location
Copy-Item "$currentDir\main.py" "$AppPath\" -Force
Copy-Item "$currentDir\requirements.txt" "$AppPath\" -Force
Copy-Item "$currentDir\README.md" "$AppPath\" -Force

# Create virtual environment
Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
Set-Location $AppPath
python -m venv .venv

# Activate virtual environment and install dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
& "$AppPath\.venv\Scripts\activate.ps1"
& "$AppPath\.venv\Scripts\pip.exe" install -r requirements.txt

# Create directories
Write-Host "Creating application directories..." -ForegroundColor Yellow
$dirs = @("uploads", "outputs", "temp", "logs")
foreach ($dir in $dirs) {
    $dirPath = Join-Path $AppPath $dir
    if (!(Test-Path $dirPath)) {
        New-Item -ItemType Directory -Path $dirPath -Force
    }
}

# Setup firewall rules (if not skipped)
if (-not $SkipFirewall) {
    Write-Host "Setting up firewall rules..." -ForegroundColor Yellow
    try {
        New-NetFirewallRule -DisplayName "HTTP Inbound" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 80 -ErrorAction SilentlyContinue
        New-NetFirewallRule -DisplayName "HTTPS Inbound" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 443 -ErrorAction SilentlyContinue
        Write-Host "Firewall rules created successfully" -ForegroundColor Green
    } catch {
        Write-Warning "Could not create firewall rules. You may need to configure them manually."
    }
}

# Check for FFmpeg
Write-Host "Checking for FFmpeg..." -ForegroundColor Yellow
try {
    $ffmpegVersion = & ffmpeg -version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "FFmpeg found and working" -ForegroundColor Green
    } else {
        Write-Warning "FFmpeg not found in PATH. Please install FFmpeg and add it to your system PATH."
    }
} catch {
    Write-Warning "FFmpeg not found. Please install FFmpeg from https://ffmpeg.org/download.html"
}

# Test the application
Write-Host "Testing the application..." -ForegroundColor Yellow
Set-Location $AppPath
$testProcess = Start-Process -FilePath "$AppPath\.venv\Scripts\uvicorn.exe" -ArgumentList "main:app --host 127.0.0.1 --port 8000" -PassThru -WindowStyle Hidden

Start-Sleep -Seconds 5

try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/" -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "Application test successful!" -ForegroundColor Green
    }
} catch {
    Write-Warning "Application test failed. Check the logs for errors."
} finally {
    if ($testProcess -and !$testProcess.HasExited) {
        $testProcess.Kill()
    }
}

Write-Host "`n=== Setup Summary ===" -ForegroundColor Green
Write-Host "Application Path: $AppPath"
Write-Host "Virtual Environment: $AppPath\.venv"
Write-Host "Python Executable: $AppPath\.venv\Scripts\python.exe"
Write-Host "Uvicorn Executable: $AppPath\.venv\Scripts\uvicorn.exe"

Write-Host "`n=== Next Steps ===" -ForegroundColor Cyan
Write-Host "1. Install NSSM (Non-Sucking Service Manager) if not already installed"
Write-Host "2. Run setup-service.ps1 to create the Windows service"
Write-Host "3. Run setup-caddy.ps1 to configure Caddy reverse proxy"
Write-Host "4. Update your domain's DNS A record to point to this server's IP"

if ($Domain) {
    Write-Host "`nDomain configured: $Domain" -ForegroundColor Yellow
    Write-Host "Make sure your DNS A record points to this server's public IP address"
}

Set-Location $currentDir
Write-Host "`nSetup completed!" -ForegroundColor Green
