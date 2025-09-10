# Test script for FFmpeg Randomizer deployment
# Run this script to verify your deployment is working correctly

param(
    [string]$Domain = "",
    [string]$LocalPort = "8000",
    [switch]$SkipHttps = $false
)

Write-Host "=== FFmpeg Randomizer Deployment Test ===" -ForegroundColor Green

# Test local API first
Write-Host "`nTesting local API (http://127.0.0.1:$LocalPort)..." -ForegroundColor Yellow

try {
    $localResponse = Invoke-WebRequest -Uri "http://127.0.0.1:$LocalPort/" -TimeoutSec 10
    if ($localResponse.StatusCode -eq 200) {
        $content = $localResponse.Content | ConvertFrom-Json
        Write-Host "✓ Local API is responding" -ForegroundColor Green
        Write-Host "  Status: $($content.status)" -ForegroundColor Cyan
        Write-Host "  FFmpeg Available: $($content.ffmpeg_available)" -ForegroundColor Cyan
        
        if (-not $content.ffmpeg_available) {
            Write-Warning "FFmpeg is not available. Some features may not work."
        }
    }
} catch {
    Write-Host "✗ Local API test failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Check if the FFmpegRandomizerAPI service is running:" -ForegroundColor Yellow
    Write-Host "  C:\nssm\nssm.exe status FFmpegRandomizerAPI" -ForegroundColor Cyan
}

# Test health endpoint
Write-Host "`nTesting health endpoint..." -ForegroundColor Yellow
try {
    $healthResponse = Invoke-WebRequest -Uri "http://127.0.0.1:$LocalPort/health" -TimeoutSec 10
    if ($healthResponse.StatusCode -eq 200) {
        $healthContent = $healthResponse.Content | ConvertFrom-Json
        Write-Host "✓ Health check passed" -ForegroundColor Green
        Write-Host "  Upload Directory: $($healthContent.upload_dir)" -ForegroundColor Cyan
        Write-Host "  Output Directory: $($healthContent.output_dir)" -ForegroundColor Cyan
    }
} catch {
    Write-Host "✗ Health check failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test effects endpoint
Write-Host "`nTesting effects endpoint..." -ForegroundColor Yellow
try {
    $effectsResponse = Invoke-WebRequest -Uri "http://127.0.0.1:$LocalPort/effects" -TimeoutSec 10
    if ($effectsResponse.StatusCode -eq 200) {
        $effectsContent = $effectsResponse.Content | ConvertFrom-Json
        Write-Host "✓ Effects endpoint working" -ForegroundColor Green
        Write-Host "  Available effects: $($effectsContent.effects.Count)" -ForegroundColor Cyan
        foreach ($effect in $effectsContent.effects) {
            Write-Host "    - $($effect.name): $($effect.description)" -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "✗ Effects endpoint failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test HTTPS if domain is provided
if ($Domain -and -not $SkipHttps) {
    Write-Host "`nTesting HTTPS endpoint (https://$Domain)..." -ForegroundColor Yellow
    
    try {
        $httpsResponse = Invoke-WebRequest -Uri "https://$Domain/" -TimeoutSec 30
        if ($httpsResponse.StatusCode -eq 200) {
            $httpsContent = $httpsResponse.Content | ConvertFrom-Json
            Write-Host "✓ HTTPS endpoint is working" -ForegroundColor Green
            Write-Host "  Status: $($httpsContent.status)" -ForegroundColor Cyan
            Write-Host "  Certificate: Valid (Let's Encrypt)" -ForegroundColor Cyan
        }
    } catch {
        Write-Host "✗ HTTPS test failed: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "This could be due to:" -ForegroundColor Yellow
        Write-Host "  - DNS not yet propagated" -ForegroundColor Gray
        Write-Host "  - Certificate still being issued" -ForegroundColor Gray
        Write-Host "  - Caddy service not running" -ForegroundColor Gray
        Write-Host "Check Caddy service status:" -ForegroundColor Yellow
        Write-Host "  C:\nssm\nssm.exe status Caddy" -ForegroundColor Cyan
    }
    
    # Test API documentation
    Write-Host "`nTesting API documentation..." -ForegroundColor Yellow
    try {
        $docsResponse = Invoke-WebRequest -Uri "https://$Domain/docs" -TimeoutSec 30
        if ($docsResponse.StatusCode -eq 200) {
            Write-Host "✓ API documentation is accessible" -ForegroundColor Green
            Write-Host "  URL: https://$Domain/docs" -ForegroundColor Cyan
        }
    } catch {
        Write-Host "✗ API documentation test failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Check Windows services
Write-Host "`nChecking Windows services..." -ForegroundColor Yellow

$apiService = Get-Service -Name "FFmpegRandomizerAPI" -ErrorAction SilentlyContinue
if ($apiService) {
    if ($apiService.Status -eq "Running") {
        Write-Host "✓ FFmpegRandomizerAPI service is running" -ForegroundColor Green
    } else {
        Write-Host "✗ FFmpegRandomizerAPI service is not running (Status: $($apiService.Status))" -ForegroundColor Red
    }
} else {
    Write-Host "✗ FFmpegRandomizerAPI service not found" -ForegroundColor Red
}

$caddyService = Get-Service -Name "Caddy" -ErrorAction SilentlyContinue
if ($caddyService) {
    if ($caddyService.Status -eq "Running") {
        Write-Host "✓ Caddy service is running" -ForegroundColor Green
    } else {
        Write-Host "✗ Caddy service is not running (Status: $($caddyService.Status))" -ForegroundColor Red
    }
} else {
    Write-Host "✗ Caddy service not found" -ForegroundColor Red
}

# Check FFmpeg
Write-Host "`nChecking FFmpeg installation..." -ForegroundColor Yellow
try {
    $ffmpegVersion = & ffmpeg -version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ FFmpeg is installed and accessible" -ForegroundColor Green
        $versionLine = ($ffmpegVersion -split "`n")[0]
        Write-Host "  $versionLine" -ForegroundColor Cyan
    } else {
        Write-Host "✗ FFmpeg not working properly" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ FFmpeg not found in PATH" -ForegroundColor Red
    Write-Host "Install FFmpeg and add it to your system PATH" -ForegroundColor Yellow
}

# Check directories
Write-Host "`nChecking application directories..." -ForegroundColor Yellow
$appPath = "C:\apps\ffmpeg-randomizer"
$directories = @("uploads", "outputs", "temp", "logs")

foreach ($dir in $directories) {
    $dirPath = Join-Path $appPath $dir
    if (Test-Path $dirPath) {
        Write-Host "✓ Directory exists: $dirPath" -ForegroundColor Green
    } else {
        Write-Host "✗ Directory missing: $dirPath" -ForegroundColor Red
    }
}

# Summary
Write-Host "`n=== Test Summary ===" -ForegroundColor Green

if ($Domain) {
    Write-Host "Your API should be available at:" -ForegroundColor Cyan
    Write-Host "  • API: https://$Domain/" -ForegroundColor White
    Write-Host "  • Documentation: https://$Domain/docs" -ForegroundColor White
    Write-Host "  • Health Check: https://$Domain/health" -ForegroundColor White
} else {
    Write-Host "Local API is available at:" -ForegroundColor Cyan
    Write-Host "  • API: http://127.0.0.1:$LocalPort/" -ForegroundColor White
    Write-Host "  • Documentation: http://127.0.0.1:$LocalPort/docs" -ForegroundColor White
}

Write-Host "`nFor troubleshooting, check logs at:" -ForegroundColor Yellow
Write-Host "  • API Logs: C:\apps\ffmpeg-randomizer\logs\" -ForegroundColor Gray
Write-Host "  • Caddy Logs: C:\caddy\logs\" -ForegroundColor Gray

Write-Host "`nTest completed!" -ForegroundColor Green
