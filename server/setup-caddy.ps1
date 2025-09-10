# Caddy Reverse Proxy Setup for FFmpeg Randomizer
# Run this script as Administrator

param(
    [Parameter(Mandatory=$true)]
    [string]$Domain,
    [string]$CaddyPath = "C:\caddy",
    [string]$NSSMPath = "C:\nssm\nssm.exe",
    [string]$ApiPort = "8000"
)

Write-Host "=== Caddy Reverse Proxy Setup ===" -ForegroundColor Green

# Check if running as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Error "This script must be run as Administrator. Exiting."
    exit 1
}

# Validate domain parameter
if ([string]::IsNullOrWhiteSpace($Domain)) {
    Write-Error "Domain parameter is required. Example: -Domain 'api.example.com'"
    exit 1
}

Write-Host "Configuring Caddy for domain: $Domain" -ForegroundColor Yellow

# Create Caddy directory
if (!(Test-Path $CaddyPath)) {
    Write-Host "Creating Caddy directory: $CaddyPath" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $CaddyPath -Force
}

# Check if Caddy executable exists
$caddyExe = "$CaddyPath\caddy.exe"
if (!(Test-Path $caddyExe)) {
    Write-Host "Caddy executable not found at $caddyExe" -ForegroundColor Red
    Write-Host "Please download Caddy from https://caddyserver.com/download and place caddy.exe in $CaddyPath" -ForegroundColor Yellow
    exit 1
}

# Create Caddyfile
$caddyfileContent = @"
# FFmpeg Randomizer API Reverse Proxy Configuration
$Domain {
    # Enable gzip compression
    encode gzip

    # Reverse proxy to FastAPI application
    reverse_proxy 127.0.0.1:$ApiPort {
        # Health check
        health_uri /health
        health_interval 30s
        health_timeout 10s
        
        # Headers for better proxy handling
        header_up Host {host}
        header_up X-Real-IP {remote}
        header_up X-Forwarded-For {remote}
        header_up X-Forwarded-Proto {scheme}
    }

    # Security headers
    header {
        # Remove server information
        -Server
        
        # Security headers
        X-Content-Type-Options nosniff
        X-Frame-Options DENY
        X-XSS-Protection "1; mode=block"
        Referrer-Policy strict-origin-when-cross-origin
        
        # HSTS (uncomment for production)
        # Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
    }

    # Rate limiting (optional - uncomment if needed)
    # rate_limit {
    #     zone static_api {
    #         key {remote}
    #         events 100
    #         window 1m
    #     }
    # }

    # Logging
    log {
        output file $CaddyPath\logs\access.log {
            roll_size 10MB
            roll_keep 5
            roll_keep_for 720h
        }
        format json
    }
}

# Optional: Redirect www to non-www
www.$Domain {
    redir https://$Domain{uri} permanent
}
"@

$caddyfilePath = "$CaddyPath\Caddyfile"
Write-Host "Creating Caddyfile at: $caddyfilePath" -ForegroundColor Yellow
$caddyfileContent | Out-File -FilePath $caddyfilePath -Encoding UTF8

# Create logs directory
$logsDir = "$CaddyPath\logs"
if (!(Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir -Force
}

# Test Caddy configuration
Write-Host "Testing Caddy configuration..." -ForegroundColor Yellow
Set-Location $CaddyPath
$testResult = & $caddyExe validate --config $caddyfilePath 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Error "Caddy configuration validation failed:"
    Write-Host $testResult -ForegroundColor Red
    exit 1
} else {
    Write-Host "Caddy configuration is valid!" -ForegroundColor Green
}

# Check if NSSM is available for service creation
if (Test-Path $NSSMPath) {
    Write-Host "Setting up Caddy as Windows service..." -ForegroundColor Yellow
    
    # Stop existing Caddy service if it exists
    $existingService = Get-Service -Name "Caddy" -ErrorAction SilentlyContinue
    if ($existingService) {
        Write-Host "Stopping existing Caddy service..." -ForegroundColor Yellow
        & $NSSMPath stop Caddy
        Start-Sleep -Seconds 3
        
        Write-Host "Removing existing Caddy service..." -ForegroundColor Yellow
        & $NSSMPath remove Caddy confirm
    }
    
    # Install Caddy service
    $caddyArgs = "run --config `"$caddyfilePath`""
    & $NSSMPath install Caddy $caddyExe $caddyArgs
    
    if ($LASTEXITCODE -eq 0) {
        # Configure service settings
        & $NSSMPath set Caddy AppDirectory $CaddyPath
        & $NSSMPath set Caddy Description "Caddy Web Server - Reverse proxy for FFmpeg Randomizer API"
        & $NSSMPath set Caddy DisplayName "Caddy Web Server"
        
        # Configure logging
        & $NSSMPath set Caddy AppStdout "$logsDir\caddy-output.log"
        & $NSSMPath set Caddy AppStderr "$logsDir\caddy-error.log"
        & $NSSMPath set Caddy AppRotateFiles 1
        & $NSSMPath set Caddy AppRotateOnline 1
        & $NSSMPath set Caddy AppRotateSeconds 86400
        & $NSSMPath set Caddy AppRotateBytes 10485760
        
        # Set startup type and recovery
        & $NSSMPath set Caddy Start SERVICE_AUTO_START
        & $NSSMPath set Caddy AppExit Default Restart
        & $NSSMPath set Caddy AppRestartDelay 5000
        
        # Start the service
        Write-Host "Starting Caddy service..." -ForegroundColor Yellow
        & $NSSMPath start Caddy
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Caddy service started successfully!" -ForegroundColor Green
        } else {
            Write-Warning "Failed to start Caddy service. Check logs at: $logsDir"
        }
    } else {
        Write-Warning "Failed to install Caddy service."
    }
} else {
    Write-Host "NSSM not found. You can run Caddy manually or install NSSM to create a service." -ForegroundColor Yellow
    Write-Host "Manual start command: $caddyExe run --config `"$caddyfilePath`"" -ForegroundColor Cyan
}

# Wait and test the setup
Write-Host "`nWaiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host "Testing HTTPS endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "https://$Domain/" -TimeoutSec 30 -SkipCertificateCheck
    if ($response.StatusCode -eq 200) {
        Write-Host "HTTPS test successful!" -ForegroundColor Green
        $content = $response.Content | ConvertFrom-Json
        Write-Host "API Status: $($content.status)" -ForegroundColor Green
    }
} catch {
    Write-Warning "HTTPS test failed: $($_.Exception.Message)"
    Write-Host "This is normal if DNS hasn't propagated yet or if the certificate is still being issued." -ForegroundColor Yellow
}

Write-Host "`n=== Setup Summary ===" -ForegroundColor Green
Write-Host "Domain: $Domain"
Write-Host "Caddy Path: $CaddyPath"
Write-Host "Caddyfile: $caddyfilePath"
Write-Host "Logs Directory: $logsDir"

Write-Host "`n=== Important Notes ===" -ForegroundColor Cyan
Write-Host "1. Make sure your DNS A record points to this server's public IP"
Write-Host "2. Let's Encrypt certificate will be automatically issued and renewed"
Write-Host "3. Your API will be available at: https://$Domain/"
Write-Host "4. API documentation will be at: https://$Domain/docs"

Write-Host "`n=== Service Management ===" -ForegroundColor Cyan
if (Test-Path $NSSMPath) {
    Write-Host "Start Caddy:   $NSSMPath start Caddy"
    Write-Host "Stop Caddy:    $NSSMPath stop Caddy"
    Write-Host "Restart Caddy: $NSSMPath restart Caddy"
    Write-Host "Caddy Status:  $NSSMPath status Caddy"
}

Write-Host "`nCaddy setup completed!" -ForegroundColor Green
