"""Bridge between Orville's Python core and VS Code's JavaScript extensions.

This module manages the Node.js sidecar process that executes JS extensions
and translates JSON-RPC messages between the two runtimes.
"""

from __future__ import annotations
import json
import subprocess
import threading
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Callable
from orville_core.extensions import ExtensionContext, PermissionSet

logger = logging.getLogger("orville.extensions.bridge")

class VSCodeBridge:
    """Manages a Node.js sidecar to execute VS Code extensions."""
    
    def __init__(self, extension_id: str, extension_path: Path, context: ExtensionContext):
        self.extension_id = extension_id
        self.extension_path = extension_path
        self.context = context
        self.process: Optional[subprocess.Popen] = None
        self._handlers: Dict[str, Callable] = {}
        self._running = False

    def start(self) -> bool:
        """Launches the Node.js sidecar with the polyfill shim."""
        try:
            # In a real deployment, 'orville-vscode-shim.js' would be bundled with the app
            shim_path = Path("assets/shims/orville-vscode-shim.js")
            
            # Launch Node.js process
            # We pass the extension path and the Orville API token for communication
            self.process = subprocess.Popen(
                ["node", str(shim_path), str(self.extension_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            self._running = True
            # Start a background thread to listen for messages from the JS side
            threading.Thread(target=self._listen, daemon=True).start()
            
            logger.info(f"Started VS Code bridge for {self.extension_id}")
            return True
        except Exception as e:
            logger.exception(f"Failed to start VS Code bridge: {e}")
            return False

    def _listen(self) -> None:
        """Listens for JSON-RPC calls from the JS extension (e.g., API requests)."""
        while self._running and self.process:
            line = self.process.stdout.readline()
            if not line:
                break
            
            try:
                message = json.loads(line)
                if message.get("type") == "request":
                    self._handle_request(message)
            except json.JSONDecodeError:
                logger.warning(f"Received malformed JSON from bridge: {line}")

    def _handle_request(self, message: Dict[str, Any]) -> None:
        """Translates JS API calls to Orville core actions."""
        method = message.get("method")
        params = message.get("params", {})
        req_id = message.get("id")

        # Example: vscode.window.showInformationMessage -> Orville Notification
        if method == "window.showInformationMessage":
            logger.info(f"Extension {self.extension_id} notification: {params.get('message')}")
            self._send_response(req_id, {"status": "sent"})
        
        elif method == "workspace.fs.readFile":
            # Check permissions before allowing file access
            if "read:workspace" in self.context.granted.scopes:
                # Logic to read file and return content
                self._send_response(req_id, {"content": "File content from Orville"})
            else:
                self._send_response(req_id, {"error": "Permission Denied"}, is_error=True)
        
        else:
            self._send_response(req_id, {"error": f"Method {method} not implemented"}, is_error=True)

    def execute_command(self, command_id: str, args: Dict[str, Any] = {}) -> Any:
        """Sends a command to the JS extension to execute."""
        if not self._running:
            raise RuntimeError("Bridge is not running")
            
        payload = {
            "type": "command",
            "command": command_id,
            "args": args
        }
        
        self.process.stdin.write(json.dumps(payload) + "\n")
        self.process.stdin.flush()
        
        # In a full implementation, we would wait for a correlated response ID
        return {"status": "command_sent"}

    def _send_response(self, req_id: Any, result: Dict[str, Any], is_error: bool = False) -> None:
        response = {
            "type": "response",
            "id": req_id,
            "result": result if not is_error else None,
            "error": result if is_error else None
        }
        self.process.stdin.write(json.dumps(response) + "\n")
        self.process.stdin.flush()

    def stop(self) -> None:
        self._running = False
        if self.process:
            self.process.terminate()
