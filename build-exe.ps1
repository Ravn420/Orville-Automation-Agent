# Orville Windows EXE Build Script
# Run this script to build a standalone Windows executable

Write-Host "Building Orville Windows Executable..." -ForegroundColor Cyan

# Step 1: Verify prerequisites
Write-Host "`n[Step 1/5] Checking prerequisites..." -ForegroundColor Yellow

# Use virtual environment Python if available
$pythonCmd = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }
$pipCmd = if (Test-Path ".venv\Scripts\pip.exe") { ".venv\Scripts\pip.exe" } else { "pip" }

$pythonVersion = & $pythonCmd --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python not found. Please install Python 3.12+" -ForegroundColor Red
    exit 1
}
Write-Host "  ✓ Found $pythonVersion" -ForegroundColor Green

# Check for PyInstaller
$pyinstaller = & $pipCmd show pyinstaller 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Installing PyInstaller..." -ForegroundColor Yellow
    & $pipCmd install "pyinstaller>=6.0"
}

# Check for required dependencies
Write-Host "  Checking dependencies..." -ForegroundColor Yellow
& $pipCmd install -e ".[api]" | Out-Null
& $pipCmd install "websockify>=0.11.0" | Out-Null
Write-Host "  ✓ Dependencies installed" -ForegroundColor Green

# Step 2: Run tests
Write-Host "`n[Step 2/5] Running test suite..." -ForegroundColor Yellow
& $pythonCmd -m pytest tests/ -q --tb=short -x
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
& $pythonCmd -m PyInstaller --noconfirm --clean $specFile

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "  ✓ Build complete" -ForegroundColor Green

# Step 5: Verify and test
Write-Host "`n[Step 5/5] Verifying build..." -ForegroundColor Yellow

# Check for the expected executable name from spec file
$exePath = "dist\Orville.exe"
if (-not (Test-Path $exePath)) {
    # Fallback: check if any .exe was created in dist
    $exes = Get-ChildItem dist\ -Filter "*.exe"
    if ($exes) {
        $exePath = $exes[0].FullName
        Write-Host "  ✓ Found executable: $exePath" -ForegroundColor Green
    } else {
        Write-Host "ERROR: No executable found in dist/" -ForegroundColor Red
        exit 1
    }
}

$exeSize = (Get-Item $exePath).Length / 1MB
Write-Host "  ✓ Executable created: $exePath" -ForegroundColor Green
Write-Host "  Size: $([math]::Round($exeSize, 2)) MB" -ForegroundColor Gray

# List bundled files if directory exists
$distDir = Join-Path (Split-Path $exePath -Parent) (Split-Path $exePath -LeafBase)
if (Test-Path $distDir) {
    Write-Host "`n  Bundled files:" -ForegroundColor Gray
    Get-ChildItem $distDir -File | Select-Object -First 10 | ForEach-Object {
        Write-Host "    - $($_.Name)" -ForegroundColor Gray
    }
}

Write-Host "`n✅ Build successful!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "  1. Test the executable: .\dist\Orville.exe" -ForegroundColor White
Write-Host "  2. Check for missing dependencies" -ForegroundColor White
Write-Host "  3. Test VNC/browser integration manually" -ForegroundColor White
Write-Host "  4. Deploy to target system" -ForegroundColor White
