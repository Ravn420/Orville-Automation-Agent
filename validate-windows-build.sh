#!/bin/bash
# Windows Build Validation Script (bash version)
# Performs smoke tests on the generated Orville executable

EXE_PATH="${1:-dist/Orville-GUI.exe}"
SKIP_LAUNCH="${2:-true}"

echo "Windows Build Validation"
echo "========================"

# Step 1: Verify executable exists
echo ""
echo "[Step 1/5] Verifying executable exists..."
if [ ! -f "$EXE_PATH" ]; then
    echo "ERROR: Executable not found at $EXE_PATH"
    exit 1
fi

EXE_SIZE=$(du -h "$EXE_PATH" | cut -f1)
EXE_BYTES=$(stat -c%s "$EXE_PATH")
# Use awk instead of bc for better portability
EXE_MB=$(awk "BEGIN {printf \"%.2f\", $EXE_BYTES / 1048576}")
echo "  ✓ Found: $EXE_PATH"
echo "  Size: $EXE_SIZE ($EXE_MB MB)"

# Step 2: Check file signature and basic properties
echo ""
echo "[Step 2/5] Checking file properties..."

# Check if it's a valid PE executable (MZ header)
if [ "$(head -c 2 "$EXE_PATH" | od -A n -t x1 | tr -d ' ')" = "4d5a" ]; then
    echo "  ✓ Valid PE executable signature (MZ header)"
else
    echo "  WARNING: Invalid PE signature"
fi

# Step 3: Check bundled resources
echo ""
echo "[Step 3/5] Checking bundled resources..."
DIST_DIR=$(dirname "$EXE_PATH")/$(basename "$EXE_PATH" .exe)

if [ -d "$DIST_DIR" ]; then
    RESOURCE_COUNT=$(find "$DIST_DIR" -type f | wc -l)
    echo "  ✓ Bundled resources: $RESOURCE_COUNT files"
    
    # Check for critical files
    CRITICAL_FILES=("icon.ico" ".env.production" "orville_core")
    
    for file in "${CRITICAL_FILES[@]}"; do
        if [ -e "$DIST_DIR/$file" ]; then
            echo "    ✓ Found: $file"
        else
            echo "    ⚠ Missing: $file"
        fi
    done
    
    # Check for noVNC assets
    if [ -d "$DIST_DIR/orville/gui/novnc" ]; then
        NOVNC_COUNT=$(find "$DIST_DIR/orville/gui/novnc" -type f | wc -l)
        echo "    ✓ noVNC assets: $NOVNC_COUNT files"
    else
        echo "    ⚠ noVNC assets not found"
    fi
else
    echo "  ℹ Single-file executable (no resource directory)"
fi

# Step 4: Check dependencies
echo ""
echo "[Step 4/5] Checking dependencies..."
REQUIRED_MODULES=("fastapi" "uvicorn" "websockify" "cryptography" "requests")
MISSING_MODULES=()

# Use virtual environment pip if available
if [ -f ".venv/Scripts/pip.exe" ]; then
    PIP_CMD=".venv/Scripts/pip.exe"
elif [ -f ".venv/bin/pip" ]; then
    PIP_CMD=".venv/bin/pip"
else
    PIP_CMD="pip"
fi

for module in "${REQUIRED_MODULES[@]}"; do
    if $PIP_CMD show "$module" > /dev/null 2>&1; then
        echo "    ✓ $module"
    else
        echo "    ✗ $module (not in build environment)"
        MISSING_MODULES+=("$module")
    fi
done

if [ ${#MISSING_MODULES[@]} -gt 0 ]; then
    echo "  WARNING: Some dependencies missing from build environment"
fi

# Step 5: Basic launch test (if not skipped)
echo ""
echo "[Step 5/5] Basic launch test..."
if [ "$SKIP_LAUNCH" = "true" ]; then
    echo "  ℹ Launch test skipped (set SKIP_LAUNCH=false to enable)"
else
    echo "  Attempting to launch executable (will close automatically)..."
    echo "  Note: This may show a window briefly"
    
    # Launch in background and capture PID
    "$EXE_PATH" > /dev/null 2>&1 &
    PID=$!
    
    if [ -n "$PID" ]; then
        echo "  ✓ Process started (PID: $PID)"
        
        # Wait briefly to see if it crashes immediately
        sleep 3
        
        if ps -p $PID > /dev/null 2>&1; then
            echo "  ✓ Process still running after 3 seconds"
            echo "  Stopping test process..."
            kill $PID 2>/dev/null
        else
            echo "  ✗ Process exited quickly"
            echo "  This may indicate missing dependencies or runtime errors"
        fi
    else
        echo "  ✗ Launch failed"
    fi
fi

# Summary
echo ""
echo "========================="
echo "Validation Complete"
echo "========================="
echo ""
echo "Executable: $EXE_PATH"
echo "Size: $EXE_MB MB"

if [ ${#MISSING_MODULES[@]} -eq 0 ]; then
    echo "Status: ✓ Build appears valid"
else
    echo "Status: ⚠ Build may have missing dependencies"
fi

echo ""
echo "Next steps:"
echo "  1. Test GUI functionality manually"
echo "  2. Test API startup and connectivity"
echo "  3. Test browser/VNC integration"
echo "  4. Test on clean Windows system"
