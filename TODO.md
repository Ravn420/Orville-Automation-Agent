# Orville Project - Focused TODO

**Project:** Orville — Autonomous Multi-Agent Orchestration and Code-Generation Framework  
**Status:** Active Development  
**Last Updated:** 2026-09-02  
**Document Focus:** Only actionable items that remain to be completed

---

## 🔴 CRITICAL - EXE Build Blockers

These issues **must** be fixed before building to EXE:

### 1. Missing freeze_support() (CRITICAL)
**File:** `windows_gui.py:1093`  
**Issue:** PyInstaller on Windows requires `multiprocessing.freeze_support()`

**Fix:**
```python
# In main() function, add:
from multiprocessing import freeze_support

def main() -> None:
    freeze_support()  # Add this line first
    app = OrvilleWindow()
    app.mainloop()
```

### 2. Hardcoded Path References (CRITICAL)
**File:** `windows_gui.py` - Throughout  
**Issue:** `Path(__file__)` won't work in frozen executables

**Fix Needed:** Add helper function and replace all path references:
```python
# Add at top of windows_gui.py
import sys
from pathlib import Path

def get_base_path() -> Path:
    """Get base path that works in both development and PyInstaller frozen apps."""
    if getattr(sys, '_MEIPASS', None):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent

# Replace ALL occurrences:
# Old: Path(__file__).resolve().parent / "filename"
# New: get_base_path() / "filename"
```

### 3. sys.executable Path Issues (CRITICAL)
**File:** `windows_gui.py:load_env()` - Line ~1039  
**Issue:** `Path(sys.executable)` incorrect in frozen apps

**Fix:** Replace with:
```python
base_dir = get_base_path()  # Use helper instead of sys.executable
```

### 4. External Dependencies Not Bundled (MEDIUM)
**Issue:** `.env.production`, `icon.ico`, `websockify` must be included

**Action Required:**
- Create `requirements.txt` with dependencies
- Update PyInstaller spec to include data files
- Ensure websockify is available (pip install websockify)

**PyInstaller Command:**
```bash
pyinstaller --noconfirm --clean --name "Orville" \
  --add-data ".env.production;." \
  --add-data "icon.ico;." \
  --hidden-import=websockify \
  --add-data "orville/gui/novnc;orville/gui/novnc" \
  windows_gui.py
```

---

## ⚠️ Incomplete Features

### 5. Browser Integration (Placeholder Only)
**File:** `windows_gui.py`  
**Status:** UI exists, backend minimal  
**Need:** Implement actual VNC/WebSocket streaming

### 6. Real-Time Streaming SSE (Incomplete)
**File:** `orville_core/api.py` - Events endpoints  
**Status:** Structure present, minimal implementation  
**Need:** Complete Server-Sent Events implementation

### 7. Knowledge Management UI Disconnect
**File:** `windows_gui.py`  
**Status:** UI exists  
**Issue:** Backend integration unclear / not implemented

---

## 📋 Pre-EXE Build Checklist

**Must Complete:**
- [ ] Add `freeze_support()` to `windows_gui.py:main()`
- [ ] Create `get_base_path()` helper function
- [ ] Replace ALL `Path(__file__)` throughout codebase
- [ ] Replace `Path(sys.executable)` in `load_env()`
- [ ] Create `requirements.txt`
- [ ] Update PyInstaller spec file
- [ ] Install websockify: `pip install websockify`
- [ ] Test PyInstaller build locally
- [ ] Test resulting EXE runs without errors

**Should Complete:**
- [ ] Add comprehensive error handling for VNC/WebSockify startup
- [ ] Implement placeholder methods in core modules (`browser.py`, `browser_relay.py`)
- [ ] Create project setup documentation (`README.md`)
- [ ] Add docstrings to major functions

**Should Review:**
- [ ] Security: Path traversal checks in file operations
- [ ] Error handling: User-friendly messages instead of silent failures
- [ ] Documentation: Missing docstrings in many modules

---

## 📦 Requirements File

Create `requirements.txt`:
```
# Core Dependencies
websockify>=0.11.0
tkinter
pathlib

# Development
pytest
pyinstaller

# API Server (if building with backend)
fastapi
uvicorn
python-multipart
```

---

## 🛡️ Security Considerations

**Need to Address:**
- File path validation (prevent directory traversal)
- Secret handling validation
- User input sanitization at API boundaries

---

## 📚 Documentation Needed

**Missing:**
- `README.md` - Project setup and usage
- `docs/SETUP.md` - Installation instructions
- `docs/BUILD.md` - Building to EXE guide
- API documentation for `orville_core/api.py`

---

## 🎯 Focus Priority

**Week 1: EXE Build Readiness**
1. Fix all PyInstaller compatibility issues
2. Create requirements.txt
3. Build and test EXE

**Week 2: Feature Completion**
1. Implement placeholder methods in core modules
2. Add error handling
3. Create basic documentation

**Week 3: Polish**
1. Add comprehensive docstrings
2. Security review
3. Performance optimization

---

## ✅ Blocked Items

**Blocked:**
- Walkthrough video archival (requires video source/metadata)
  - See: `docs/WALKTHROUGH_VIDEO_ARCHIVAL_COMPLIANCE_NOTE.md`
  - Needs: Original video file or regeneration

---

## 📝 Notes

- Focus on **critical EXE blockers first** - nothing else matters if EXE doesn't build
- Test EXE build frequently to catch issues early
- Document as you go - don't leave it all to the end
- Current test suite: **788 passed, 1 warning** (good foundation)
- Keep `.gitignore` updated with build artifacts

---

**Document Version:** 1.0  
**Next Review:** After EXE build succeeds  
**Owner:** Orchestration Agent
