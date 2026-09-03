# Orville Windows EXE Build Script
# Run this script to build a standalone Windows executable

Write-Host "Building Orville Windows Executable..." -ForegroundColor Cyan

# Step 1: Verify prerequisites
Write-Host "`n[Step 1/5] Checking prerequisites..." -ForegroundColor Yellow

$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python not found. Please install Python 3.12+" -ForegroundColor Red
    exit 1
}
Write-Host "  ✓ Found $pythonVersion" -ForegroundColor Green

# Check for PyInstaller
$pyinstaller = pip show pyinstaller 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Installing PyInstaller..." -ForegroundColor Yellow
    pip install "pyinstaller>=6.0"
}

# Check for required dependencies
Write-Host "  Checking dependencies..." -ForegroundColor Yellow
pip install -e ".[api]" | Out-Null
pip install "websockify>=0.11.0" | Out-Null
Write-Host "  ✓ Dependencies installed" -ForegroundColor Green

# Step 2: Run tests
Write-Host "`n[Step 2/5] Running test suite..." -ForegroundColor Yellow
python -m pytest tests/ -q --tb=short -x
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: Some tests failed. Continue anyway? (Y/N)" -ForegroundColor Yellow
    $response = Read-Host
    if ($response -ne 'Y') {
        exit 1
    }
}

# Step 3: Clean previous builds
Write-Host "`n[Step 3/5] Cleaning previous builds..." -ForegroundColor Yellow
$buildDirs = @('build', 'dist', '__pycache__', '*.egg-info')
foreach ($dir in $buildDirs) {
    if (Test-Path $dir) {
        Remove-Item -Path $dir -Recurse -Force -ErrorAction SilentlyContinue
    }
}
Write-Host "  ✓ Cleaned" -ForegroundColor Green

# Step 4: Build executable
Write-Host "`n[Step 4/5] Building executable..." -ForegroundColor Yellow

# Use the fixed spec file
$specFile = "Orville-GUI-Final-Fixed.spec"

if (-not (Test-Path $specFile)) {
    Write-Host "ERROR: Spec file not found: $specFile" -ForegroundColor Red
    exit 1
}

Write-Host "  Using spec file: $specFile" -ForegroundColor Gray
pyinstaller --noconfirm --clean $specFile

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "  ✓ Build complete" -ForegroundColor Green

# Step 5: Verify and test
Write-Host "`n[Step 5/5] Verifying build..." -ForegroundColor Yellow

$exePath = "dist\Orville.exe"
if (-not (Test-Path $exePath)) {
    Write-Host "ERROR: Executable not found at $exePath" -ForegroundColor Red
    exit 1
}

$exeSize = (Get-Item $exePath).Length / 1MB
Write-Host "  ✓ Executable created: $exePath" -ForegroundColor Green
Write-Host "  Size: $([math]::Round($exeSize, 2)) MB" -ForegroundColor Gray

# List bundled files
Write-Host "`n  Bundled files:" -ForegroundColor Gray
Get-ChildItem dist\Orville\ -File | Select-Object -First 10 | ForEach-Object {
    Write-Host "    - $($_.Name)" -ForegroundColor Gray
}

Write-Host "`n✅ Build successful!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "  1. Test the executable: .\dist\Orville.exe" -ForegroundColor White
Write-Host "  2. Check for missing dependencies" -ForegroundColor White
Write-Host "  3. Test VNC/browser integration manually" -ForegroundColor White
Write-Host "  4. Deploy to target system" -ForegroundColor White
