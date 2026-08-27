"""Independent local security review and clean-environment integration check.

This checker uses synthetic credentials only. It verifies the public redaction
boundary and imports the package in a subprocess with a minimal environment;
it does not contact providers or require credentials.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    probe = f"import sys, importlib.util; s=importlib.util.spec_from_file_location('orville_security', {str(root / 'orville_core' / 'security.py')!r}); m=importlib.util.module_from_spec(s); sys.modules['orville_security']=m; s.loader.exec_module(m); v=m.SecretRedactor.redact({{'api_key':'sk_review_synthetic','message':'Bearer tok_review_synthetic'}}); assert 'sk_review_synthetic' not in str(v) and 'tok_review_synthetic' not in str(v); print('redaction-ok')"
    env = {"PATH": os.environ.get("PATH", ""), "PYTHONPATH": str(root)}
    result = subprocess.run([sys.executable, "-I", "-c", probe], cwd=root, env=env, capture_output=True, text=True, check=False)
    if result.returncode != 0 or "redaction-ok" not in result.stdout:
        print(json.dumps({"passed": False, "check": "clean_import_and_redaction", "stderr": result.stderr[-500:]}, sort_keys=True))
        return 2
    print(json.dumps({"passed": True, "checks": ["independent_redaction_boundary", "clean_environment_import"], "credentials_used": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
