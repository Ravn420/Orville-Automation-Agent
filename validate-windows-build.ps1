# Windows Build Validation Script
# Performs smoke tests on the generated Orville executable

param(
    [string]$ExePath = "dist\Orville.exe",
    [switch]$SkipLaunch
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "Windows Build Validation" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan

# Step 1: Verify executable exists
Write-Host "`n[Step 1/5] Verifying executable exists..." -ForegroundColor Yellow
if (-not (Test-Path $ExePath)) {
    Write-Host "ERROR: Executable not found at $ExePath" -ForegroundColor Red
    exit 1
}

$exeInfo = Get-Item $ExePath
$exeSize = [math]::Round($exeInfo.Length / 1MB, 2)
Write-Host "  Found: $ExePath" -ForegroundColor Green
Write-Host "  Size: $exeSize MB" -ForegroundColor Gray
Write-Host "  Modified: $($exeInfo.LastWriteTime)" -ForegroundColor Gray

# Step 2: Check file signature and basic properties
Write-Host "`n[Step 2/5] Checking file properties..." -ForegroundColor Yellow
try {
    $fileSignature = Get-AuthenticodeSignature $ExePath -ErrorAction SilentlyContinue
    if ($fileSignature) {
        Write-Host "  Signature Status: $($fileSignature.Status)" -ForegroundColor Gray
    }
} catch {
    Write-Host "  Signature check skipped (unsigned or no tools)" -ForegroundColor Gray
}

# Check if it's a valid PE executable
$peBytes = [System.IO.File]::ReadAllBytes($ExePath)
if ($peBytes[0] -eq 0x4D -and $peBytes[1] -eq 0x5A) {
    Write-Host "  Valid PE executable signature" -ForegroundColor Green
} else {
    Write-Host "  WARNING: Invalid PE signature" -ForegroundColor Yellow
}

# Step 3: Check bundled resources
Write-Host "`n[Step 3/5] Checking bundled resources..." -ForegroundColor Yellow
$distDir = Join-Path (Split-Path $ExePath -Parent) (Split-Path $ExePath -LeafBase)
if (Test-Path $distDir) {
    $resourceCount = (Get-ChildItem $distDir -Recurse -File).Count
    Write-Host "  Bundled resources: $resourceCount files" -ForegroundColor Green
    
    # Check for critical files
    $criticalFiles = @("icon.ico", ".env.production", "orville_core")
    
    foreach ($file in $criticalFiles) {
        $path = Join-Path $distDir $file
        if (Test-Path $path) {
            Write-Host "    Found: $file" -ForegroundColor Green
        } else {
            Write-Host "    Missing: $file" -ForegroundColor Yellow
        }
    }
    
    # Check for noVNC assets
    $novncPath = Join-Path $distDir "orville\gui\novnc"
    if (Test-Path $novncPath) {
        $novncCount = (Get-ChildItem $novncPath -Recurse -File).Count
        Write-Host "    noVNC assets: $novncCount files" -ForegroundColor Green
    } else {
        Write-Host "    noVNC assets not found" -ForegroundColor Yellow
    }
} else {
    Write-Host "  Single-file executable (no resource directory)" -ForegroundColor Gray
}

# Step 4: Check dependencies
Write-Host "`n[Step 4/5] Checking dependencies..." -ForegroundColor Yellow
$requiredModules = @("fastapi", "uvicorn", "websockify", "cryptography", "requests")
$missingModules = @()

# We can't directly check imports in frozen exe, but we can verify the build environment
$pythonCmd = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }
$pipCmd = if (Test-Path ".venv\Scripts\pip.exe") { ".venv\Scripts\pip.exe" } else { "pip" }

foreach ($module in $requiredModules) {
    $result = & $pipCmd show $module 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    $module" -ForegroundColor Green
    } else {
        Write-Host "    $module (not in build environment)" -ForegroundColor Red
        $missingModules += $module
    }
}

if ($missingModules.Count -gt 0) {
    Write-Host "  WARNING: Some dependencies missing from build environment" -ForegroundColor Yellow
}

# Step 5: Basic launch test (if not skipped)
Write-Host "`n[Step 5/5] Basic launch test..." -ForegroundColor Yellow
if ($SkipLaunch) {
    Write-Host "  Launch test skipped (use -SkipLaunch `$false to enable)" -ForegroundColor Gray
} else {
    Write-Host "  Attempting to launch executable (will close automatically)..." -ForegroundColor Gray
    Write-Host "  Note: This may show a window briefly" -ForegroundColor Gray
    
    try {
        $process = Start-Process $ExePath -PassThru -WindowStyle Normal
        Write-Host "  Process started (PID: $($process.Id))" -ForegroundColor Green
        
        # Wait briefly to see if it crashes immediately
        Start-Sleep -Seconds 3
        
        if ($process.HasExited) {
            Write-Host "  Process exited quickly (exit code: $($process.ExitCode))" -ForegroundColor Red
            Write-Host "  This may indicate missing dependencies or runtime errors" -ForegroundColor Yellow
        } else {
            Write-Host "  Process still running after 3 seconds" -ForegroundColor Green
            Write-Host "  Stopping test process..." -ForegroundColor Gray
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        }
    } catch {
        Write-Host "  Launch failed: $_" -ForegroundColor Red
    }
}

# Summary
Write-Host "`n=========================" -ForegroundColor Cyan
Write-Host "Validation Complete" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan

Write-Host "`nExecutable: $ExePath" -ForegroundColor White
Write-Host "Size: $exeSize MB" -ForegroundColor White

if ($missingModules.Count -eq 0) {
    Write-Host "Status: Build appears valid" -ForegroundColor Green
} else {
    Write-Host "Status: Build may have missing dependencies" -ForegroundColor Yellow
}

Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "  1. Test GUI functionality manually" -ForegroundColor White
Write-Host "  2. Test API startup and connectivity" -ForegroundColor White
Write-Host "  3. Test browser/VNC integration" -ForegroundColor White
Write-Host "  4. Test on clean Windows system" -ForegroundColor White
