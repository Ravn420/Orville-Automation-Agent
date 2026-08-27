"""Safe Hugging Face Hub discovery, compatibility checks, and model downloads."""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from .local_models import LocalModelCatalog, LocalModelRecord

_REPO_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}/[A-Za-z0-9][A-Za-z0-9_.-]{0,95}$")
_DEFAULT_HUB_URL = "https://huggingface.co"
_DEFAULT_MAX_DOWNLOAD_BYTES = 20 * 1024 * 1024 * 1024


class HubModelError(RuntimeError):
    """Raised for invalid Hub requests, unavailable metadata, or unsafe downloads."""


@dataclass(frozen=True)
class MachineCapabilities:
    platform: str
    cpu_cores: int
    ram_bytes: int
    disk_free_bytes: int
    gpu_available: bool = False
    gpu_memory_bytes: int = 0
    gpu_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["ram_gb"] = round(self.ram_bytes / 1024**3, 2)
        data["disk_free_gb"] = round(self.disk_free_bytes / 1024**3, 2)
        data["gpu_memory_gb"] = round(self.gpu_memory_bytes / 1024**3, 2)
        return data


def _system_ram_bytes() -> int:
    if os.name == "nt":
        class MemoryStatus(ctypes.Structure):
            _fields_ = [("length", ctypes.c_ulong), ("memory_load", ctypes.c_ulong), ("total", ctypes.c_ulonglong), ("available", ctypes.c_ulonglong), ("total_page", ctypes.c_ulonglong), ("available_page", ctypes.c_ulonglong), ("total_virtual", ctypes.c_ulonglong), ("available_virtual", ctypes.c_ulonglong), ("available_extended", ctypes.c_ulonglong)]
        status = MemoryStatus()
        status.length = ctypes.sizeof(MemoryStatus)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return int(status.total)
    if hasattr(os, "sysconf"):
        try:
            return int(os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE"))
        except (OSError, ValueError):
            pass
    return 0


def detect_machine_capabilities(path: str | Path = ".") -> MachineCapabilities:
    gpu_available = False
    gpu_memory = 0
    gpu_name = None
    try:
        result = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=2, check=False)
        if result.returncode == 0 and result.stdout.strip():
            first = result.stdout.strip().splitlines()[0].split(",", 1)
            gpu_name = first[0].strip()
            gpu_memory = int(float(first[1].strip()) * 1024**2) if len(first) > 1 else 0
            gpu_available = True
    except (OSError, ValueError, subprocess.TimeoutExpired):
        pass
    root = Path(path).expanduser().resolve()
    return MachineCapabilities(platform=platform.platform(), cpu_cores=os.cpu_count() or 1, ram_bytes=_system_ram_bytes(), disk_free_bytes=shutil.disk_usage(root).free, gpu_available=gpu_available, gpu_memory_bytes=gpu_memory, gpu_name=gpu_name)


class HuggingFaceHubClient:
    """Small standard-library Hub client; it never executes repository code."""

    def __init__(self, *, base_url: str = _DEFAULT_HUB_URL, token: str | None = None, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout

    def _request(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        if params:
            url += "?" + urlencode({key: value for key, value in params.items() if value is not None})
        headers = {"Accept": "application/json", "User-Agent": "Orville/1.0"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        try:
            with urlopen(Request(url, headers=headers), timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise HubModelError(f"Hugging Face Hub HTTP {exc.code}: {detail[:300]}") from exc
        except (URLError, TimeoutError) as exc:
            raise HubModelError(f"Hugging Face Hub connection failed: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise HubModelError("Hugging Face Hub returned invalid JSON") from exc

    @staticmethod
    def _validate_repo_id(repo_id: str) -> str:
        if not _REPO_ID.fullmatch(repo_id.strip()):
            raise HubModelError("repo_id must use the form owner/model and contain only safe characters")
        return repo_id.strip()

    @staticmethod
    def _capabilities(info: dict[str, Any]) -> list[str]:
        values = {str(info.get("pipeline_tag", "")).lower(), *(str(tag).lower() for tag in info.get("tags", []) or [])}
        repo = str(info.get("id", "")).lower()
        capabilities: set[str] = set()
        if any(value in values for value in {"text-generation", "text2text-generation", "conversational", "text-generation-inference"}):
            capabilities.add("text")
        if any(value in values for value in {"text-to-image", "image-text-to-image", "unconditional-image-generation"}):
            capabilities.add("image_generation")
        if any(value in values for value in {"text-to-video", "video-generation"}):
            capabilities.add("video_generation")
        if any(value in values for value in {"feature-extraction", "sentence-similarity"}):
            capabilities.add("embeddings")
        if any(value in values for value in {"image-classification", "image-to-text", "visual-question-answering"}):
            capabilities.add("vision")
        if any(token in repo or token in values for token in {"code", "coder", "programming"}):
            capabilities.add("code")
        return sorted(capabilities)

    @staticmethod
    def _size_bytes(info: dict[str, Any]) -> int:
        safetensors = info.get("safetensors") or {}
        if safetensors.get("total"):
            return int(safetensors["total"])
        siblings = info.get("siblings") or []
        return sum(int((item.get("lfs") or {}).get("size") or item.get("size") or 0) for item in siblings if isinstance(item, dict))

    def _decorate(self, info: dict[str, Any], machine: MachineCapabilities) -> dict[str, Any]:
        size = self._size_bytes(info)
        required_ram = max(size * 1.25, 2 * 1024**3) if size else 0
        disk_required = int(size * 1.1) if size else 0
        reasons: list[str] = []
        if required_ram and machine.ram_bytes < required_ram:
            reasons.append(f"estimated RAM requirement is {required_ram / 1024**3:.1f} GB")
        if disk_required and machine.disk_free_bytes < disk_required:
            reasons.append(f"download requires approximately {disk_required / 1024**3:.1f} GB free disk")
        capabilities = self._capabilities(info)
        if not capabilities:
            reasons.append("Hub metadata does not declare a supported inference task")
        return {"id": info.get("id"), "model_id": info.get("id"), "author": info.get("author"), "pipeline_tag": info.get("pipeline_tag"), "tags": info.get("tags", []), "downloads": info.get("downloads", 0), "likes": info.get("likes", 0), "last_modified": info.get("lastModified"), "license": info.get("cardData", {}).get("license") if isinstance(info.get("cardData"), dict) else None, "gated": bool(info.get("gated")), "size_bytes": size, "size_gb": round(size / 1024**3, 2) if size else None, "capabilities": capabilities, "supported": not reasons, "unsupported_reasons": reasons, "machine": machine.to_dict()}

    def search(self, query: str = "", *, pipeline_tag: str | None = None, limit: int = 20, machine: MachineCapabilities | None = None, supported_only: bool = False) -> list[dict[str, Any]]:
        if not 1 <= limit <= 50:
            raise HubModelError("limit must be between 1 and 50")
        machine = machine or detect_machine_capabilities()
        raw = self._request("api/models", {"search": query.strip() or None, "pipeline_tag": pipeline_tag, "limit": limit, "sort": "downloads", "direction": -1, "full": "true"})
        models = [self._decorate(item, machine) for item in raw if isinstance(item, dict)]
        return [item for item in models if item["supported"]] if supported_only else models

    def details(self, repo_id: str, *, machine: MachineCapabilities | None = None) -> dict[str, Any]:
        repo_id = self._validate_repo_id(repo_id)
        return self._decorate(self._request(f"api/models/{quote(repo_id, safe='/')}"), machine or detect_machine_capabilities())

    def download(self, repo_id: str, destination: str | Path, *, revision: str = "main", max_bytes: int = _DEFAULT_MAX_DOWNLOAD_BYTES, catalog: LocalModelCatalog | None = None, machine: MachineCapabilities | None = None, progress: Any | None = None, cancel_event: Any | None = None, pause_event: Any | None = None) -> LocalModelRecord:
        from fnmatch import fnmatch
        repo_id = self._validate_repo_id(repo_id)
        if not 1 <= max_bytes <= _DEFAULT_MAX_DOWNLOAD_BYTES:
            raise HubModelError(f"max_bytes must be between 1 and { _DEFAULT_MAX_DOWNLOAD_BYTES}")
        raw = self._request(f"api/models/{quote(repo_id, safe='/')}")
        info = self._decorate(raw, machine or detect_machine_capabilities(destination))
        if info["size_bytes"] and info["size_bytes"] > max_bytes:
            raise HubModelError(f"model is {info['size_gb']} GB, above the configured download limit")
        root = Path(destination).expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)
        target = root / repo_id.replace("/", "__")
        target.mkdir(parents=True, exist_ok=True)
        allowed = ["*.json", "*.safetensors", "*.bin", "*.gguf", "*.model", "*.txt", "*.tokenizer*", "*.vocab", "*.merges", "*.spm", "*.tiktoken", "*.onnx", "*.pt", "*.pth", "*.msgpack", "*.h5"]
        files = [item for item in (raw.get("siblings") or []) if isinstance(item, dict) and isinstance(item.get("rfilename"), str) and any(fnmatch(item["rfilename"], pattern) for pattern in allowed)]
        total = sum(int((item.get("lfs") or {}).get("size") or item.get("size") or 0) for item in files)
        completed = 0
        for item in files:
            relative = Path(item["rfilename"])
            if relative.is_absolute() or ".." in relative.parts:
                continue
            final_path = (target / relative).resolve()
            if os.path.commonpath([str(target), str(final_path)]) != str(target):
                raise HubModelError("Hub file path escaped the model directory")
            final_path.parent.mkdir(parents=True, exist_ok=True)
            expected = int((item.get("lfs") or {}).get("size") or item.get("size") or 0)
            part_path = final_path.with_name(final_path.name + ".orville-part")
            existing = part_path.stat().st_size if part_path.exists() else 0
            if expected and existing >= expected:
                completed += expected
                continue
            headers = {"Accept": "application/octet-stream", "User-Agent": "Orville/1.0"}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            if existing:
                headers["Range"] = f"bytes={existing}-"
            url = f"{self.base_url}/{quote(repo_id, safe='/')}/resolve/{quote(revision, safe='')}/{quote(item['rfilename'], safe='/')}?download=true"
            try:
                with urlopen(Request(url, headers=headers), timeout=self.timeout) as response:
                    mode = "ab" if existing and getattr(response, "status", 200) == 206 else "wb"
                    if mode == "wb":
                        existing = 0
                    with part_path.open(mode) as handle:
                        while True:
                            if cancel_event is not None and cancel_event.is_set():
                                raise InterruptedError("download cancelled")
                            if pause_event is not None and pause_event.is_set():
                                raise DownloadPaused()
                            chunk = response.read(1024 * 1024)
                            if not chunk:
                                break
                            handle.write(chunk)
                            completed += len(chunk)
                            if progress:
                                progress(completed, total)
            except InterruptedError:
                raise
            except HTTPError as exc:
                message = f"download failed for {item['rfilename']}: {exc}"
                if exc.code in {408, 425, 429, 500, 502, 503, 504, 520, 521, 522, 523, 524}:
                    raise DownloadRetryableError(message) from exc
                raise HubModelError(message) from exc
            except (URLError, OSError) as exc:
                raise DownloadRetryableError(f"download failed for {item['rfilename']}: {exc}") from exc
            if expected and part_path.stat().st_size != expected:
                raise DownloadRetryableError(f"incomplete download for {item['rfilename']}")
            part_path.replace(final_path)
        if progress:
            progress(total or completed, total or completed)
        actual_size = sum(item.stat().st_size for item in target.rglob("*") if item.is_file())
        if actual_size > max_bytes:
            raise HubModelError("downloaded model exceeded the configured size limit")
        catalog = catalog or LocalModelCatalog(root / "orville-models.json")
        return catalog.import_model(target, model_id=repo_id, display_name=repo_id, base_model=repo_id, capabilities=info["capabilities"], license=info.get("license"), provenance={"source_type": "huggingface", "repository": repo_id, "revision": revision, "url": f"{self.base_url}/" + repo_id}, ownership={"owner_type": "local_operator", "imported_by": "orville"}, metadata={"hub_repo_id": repo_id, "revision": revision, "hub_url": f"{self.base_url}/" + repo_id, "size_bytes": actual_size, "pipeline_tag": info.get("pipeline_tag"), "gated": info.get("gated", False)})


class DownloadPaused(Exception):
    """Internal signal used to stop a download without deleting partial files."""


class DownloadRetryableError(HubModelError):
    """Transient transfer failure eligible for bounded retry with backoff."""


@dataclass
class DownloadJob:
    job_id: str
    repo_id: str
    destination: str
    revision: str
    max_bytes: int
    status: str = "queued"
    total_bytes: int = 0
    downloaded_bytes: int = 0
    progress: float = 0.0
    error: str | None = None
    model_id: str | None = None
    created_at: str = ""
    updated_at: str = ""
    cancel_requested: bool = False
    pause_requested: bool = False
    attempt_count: int = 0
    retry_count: int = 0
    max_retries: int = 3
    next_retry_at: str | None = None
    last_retry_delay_seconds: float = 0.0
    retry_telemetry: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def check_runtime_compatibility(record: LocalModelRecord | dict[str, Any], runtime: str, machine: MachineCapabilities | None = None) -> dict[str, Any]:
    """Return conservative, non-executing compatibility checks for local runtimes."""
    runtime = runtime.strip().lower().replace("-", "_")
    if runtime not in {"ollama", "llama_cpp", "transformers"}:
        raise HubModelError("runtime must be ollama, llama.cpp, or transformers")
    machine = machine or detect_machine_capabilities()
    data = record.to_dict() if isinstance(record, LocalModelRecord) else dict(record)
    path = Path(str(data.get("source_path", ""))).expanduser()
    file_format = str(data.get("file_format", "unknown")).lower()
    capabilities = set(data.get("capabilities") or [])
    metadata = data.get("metadata") or {}
    checks: dict[str, bool] = {}
    reasons: list[str] = []
    warnings: list[str] = []
    exists = path.exists()
    checks["asset_exists"] = exists
    if not exists:
        reasons.append("model asset path does not exist")
    if runtime in {"ollama", "llama_cpp"}:
        has_gguf = path.suffix.lower() == ".gguf" or (path.is_dir() and any(item.suffix.lower() == ".gguf" for item in path.rglob("*")))
        checks["gguf_format"] = file_format == "gguf" or has_gguf
        if not checks["gguf_format"]:
            reasons.append(f"{runtime.replace('_', '.')} requires a GGUF model file")
        checks["text_capability"] = bool(capabilities & {"text", "code"})
        if not checks["text_capability"]:
            warnings.append("Hub metadata does not declare text or code capability")
        if runtime == "ollama":
            checks["ollama_runtime"] = bool(shutil.which("ollama") or data.get("endpoint"))
            if not checks["ollama_runtime"]:
                warnings.append("Ollama executable or endpoint was not detected; configure it before activation")
        else:
            checks["llama_cpp_runtime"] = bool(shutil.which("llama-cli") or shutil.which("llama-server") or data.get("endpoint"))
            if not checks["llama_cpp_runtime"]:
                warnings.append("llama.cpp executable or endpoint was not detected; configure it before activation")
    else:
        checks["transformers_directory"] = path.is_dir() or file_format in {"safetensors", "bin", "directory"}
        checks["config_json"] = (path / "config.json").is_file() if path.is_dir() else False
        if not checks["transformers_directory"]:
            reasons.append("Transformers requires a model directory or supported weight file")
        if not checks["config_json"]:
            reasons.append("Transformers model directory is missing config.json")
        checks["transformers_package"] = __import__("importlib.util").util.find_spec("transformers") is not None
        if not checks["transformers_package"]:
            warnings.append("Python package 'transformers' is not installed in this runtime")
        checks["torch_or_accelerate"] = any(__import__("importlib.util").util.find_spec(name) is not None for name in ("torch", "accelerate"))
        if not checks["torch_or_accelerate"]:
            warnings.append("Neither torch nor accelerate was detected")
    required_ram = int((int(data.get("metadata", {}).get("size_bytes", 0) or 0) or 0) * 1.25)
    checks["memory_headroom"] = not required_ram or machine.ram_bytes >= required_ram
    if not checks["memory_headroom"]:
        reasons.append("estimated model memory exceeds available system RAM")
    checks["disk_available"] = machine.disk_free_bytes > 512 * 1024 * 1024
    if not checks["disk_available"]:
        reasons.append("less than 512 MB free disk space is available")
    required_gpu = bool(metadata.get("requires_gpu", False))
    checks["hardware_compatible"] = not required_gpu or machine.gpu_available
    if not checks["hardware_compatible"]:
        reasons.append("model requires a compatible GPU, but no supported GPU was detected")
    diagnostics: list[dict[str, Any]] = []
    diagnostic_map = {
        "asset_exists": "missing_asset",
        "gguf_format": "unsupported_format",
        "transformers_directory": "unsupported_format",
        "config_json": "invalid_model_config",
        "memory_headroom": "insufficient_ram",
        "disk_available": "insufficient_disk",
        "hardware_compatible": "incompatible_hardware",
    }
    for check_name, code in diagnostic_map.items():
        if checks.get(check_name) is False:
            diagnostics.append({"code": code, "message": next((reason for reason in reasons if check_name.replace("_", " ") in reason.lower()), f"compatibility check failed: {check_name}"), "severity": "error"})
    if not checks.get("ollama_runtime", True) or not checks.get("llama_cpp_runtime", True) or not checks.get("transformers_package", True) or not checks.get("torch_or_accelerate", True):
        diagnostics.append({"code": "missing_runtime", "message": "the selected runtime executable or required package is unavailable", "severity": "warning"})
    if data.get("license") or data.get("license_restrictions"):
        diagnostics.append({"code": "license_restriction", "message": "review the model license and restrictions before activation", "severity": "warning"})
    compatible = all(checks[key] for key in checks if key not in {"ollama_runtime", "llama_cpp_runtime", "transformers_package", "torch_or_accelerate"}) and not reasons
    return {"runtime": runtime, "compatible": compatible, "checks": checks, "reasons": reasons, "warnings": warnings, "diagnostics": diagnostics, "machine": machine.to_dict(), "model_id": data.get("model_id")}


class DownloadJobManager:
    """Persistent download jobs with resumable files and cooperative cancellation."""

    def __init__(self, state_path: str | Path, client: HuggingFaceHubClient, catalog: LocalModelCatalog, models_root: str | Path) -> None:
        import threading
        from uuid import uuid4
        self.state_path = Path(state_path)
        self.models_root = Path(models_root).expanduser().resolve()
        self.models_root.mkdir(parents=True, exist_ok=True)
        self.client = client
        self.catalog = catalog
        self._lock = threading.RLock()
        self._cancel: dict[str, threading.Event] = {}
        self._pause: dict[str, threading.Event] = {}
        self._jobs: dict[str, DownloadJob] = {}
        self._uuid4 = uuid4
        self._load()

    def _load(self) -> None:
        if not self.state_path.exists():
            return
        try:
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
            for item in payload.get("jobs", []):
                item = dict(item)
                item.setdefault("attempt_count", 0)
                item.setdefault("retry_count", 0)
                item.setdefault("max_retries", 3)
                item.setdefault("next_retry_at", None)
                item.setdefault("last_retry_delay_seconds", 0.0)
                item.setdefault("retry_telemetry", [])
                job = DownloadJob(**item)
                if job.status == "running":
                    job.status = "paused"
                    job.error = "Orville restarted; resume this job to continue"
                self._jobs[job.job_id] = job
        except (OSError, ValueError, TypeError):
            self._jobs = {}

    def _save(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        temporary.write_text(json.dumps({"schema_version": 1, "jobs": [job.to_dict() for job in self._jobs.values()]}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(self.state_path)

    def list(self) -> list[DownloadJob]:
        with self._lock:
            return list(self._jobs.values())

    def get(self, job_id: str) -> DownloadJob:
        with self._lock:
            if job_id not in self._jobs:
                raise KeyError(job_id)
            return self._jobs[job_id]

    def _update(self, job: DownloadJob, **changes: Any) -> None:
        from datetime import UTC, datetime
        with self._lock:
            for key, value in changes.items():
                setattr(job, key, value)
            job.updated_at = datetime.now(UTC).isoformat()
            self._save()

    def start(self, repo_id: str, *, destination: str | Path | None = None, revision: str = "main", max_bytes: int = _DEFAULT_MAX_DOWNLOAD_BYTES, max_retries: int = 3) -> DownloadJob:
        from datetime import UTC, datetime
        from threading import Event, Thread
        repo_id = self.client._validate_repo_id(repo_id)
        info = self.client.details(repo_id, machine=detect_machine_capabilities(self.models_root))
        if not 0 <= max_retries <= 5:
            raise HubModelError("max_retries must be between 0 and 5")
        if info["size_bytes"] and info["size_bytes"] > max_bytes:
            raise HubModelError(f"model is {info['size_gb']} GB, above the configured download limit")
        root = Path(destination or self.models_root).expanduser().resolve()
        if os.path.commonpath([str(self.models_root), str(root)]) != str(self.models_root):
            raise HubModelError("download destination must remain inside Orville's models directory")
        root.mkdir(parents=True, exist_ok=True)
        job_id = f"download-{self._uuid4().hex[:12]}"
        now = datetime.now(UTC).isoformat()
        job = DownloadJob(job_id, repo_id, str(root), revision, max_bytes, total_bytes=info["size_bytes"], max_retries=max_retries, created_at=now, updated_at=now)
        with self._lock:
            self._jobs[job_id] = job
            self._cancel[job_id] = Event()
            self._pause[job_id] = Event()
            self._save()
        Thread(target=self._run, args=(job, info), daemon=True, name=f"orville-download-{job_id}").start()
        return job

    def resume(self, job_id: str) -> DownloadJob:
        from threading import Event, Thread
        job = self.get(job_id)
        if job.status not in {"paused", "cancelled", "failed"}:
            return job
        info = self.client.details(job.repo_id, machine=detect_machine_capabilities(self.models_root))
        with self._lock:
            self._cancel[job_id] = Event()
            self._pause[job_id] = Event()
        self._update(job, status="queued", error=None, cancel_requested=False, pause_requested=False, retry_count=0, next_retry_at=None, last_retry_delay_seconds=0.0)
        Thread(target=self._run, args=(job, info), daemon=True, name=f"orville-download-{job_id}").start()
        return job

    def pause(self, job_id: str) -> DownloadJob:
        job = self.get(job_id)
        if job.status in {"completed", "failed", "cancelled", "paused"}:
            return job
        self._pause.setdefault(job_id, __import__("threading").Event()).set()
        self._update(job, pause_requested=True, status="pausing")
        return job

    def cancel(self, job_id: str) -> DownloadJob:
        job = self.get(job_id)
        if job.status in {"completed", "failed", "cancelled"}:
            return job
        self._cancel.setdefault(job_id, __import__("threading").Event()).set()
        self._update(job, cancel_requested=True, status="cancelling")

        return job

    def _run(self, job: DownloadJob, info: dict[str, Any]) -> None:
        self._update(job, status="running", next_retry_at=None)
        def progress(downloaded: int, total: int) -> None:
            self._update(job, downloaded_bytes=downloaded, total_bytes=total or job.total_bytes, progress=min(1.0, downloaded / (total or job.total_bytes)) if (total or job.total_bytes) else 0.0)
        while True:
            try:
                self._update(job, attempt_count=job.attempt_count + 1, status="running", next_retry_at=None)
                record = self.client.download(job.repo_id, job.destination, revision=job.revision, max_bytes=job.max_bytes, catalog=self.catalog, machine=detect_machine_capabilities(self.models_root), progress=progress, cancel_event=self._cancel[job.job_id], pause_event=self._pause[job.job_id])
                self._update(job, status="completed", downloaded_bytes=job.total_bytes or job.downloaded_bytes, progress=1.0, model_id=record.model_id, cancel_requested=False, pause_requested=False, next_retry_at=None)
                return
            except DownloadPaused:
                self._update(job, status="paused", error="download paused; partial files retained for resume", pause_requested=False, next_retry_at=None)
                return
            except InterruptedError:
                self._update(job, status="cancelled", error="download cancelled; partial files retained for resume", cancel_requested=False, next_retry_at=None)
                return
            except DownloadRetryableError as exc:
                if job.retry_count >= job.max_retries:
                    self._update(job, status="failed", error=str(exc), next_retry_at=None)
                    return
                retry_number = job.retry_count + 1
                delay = min(60.0, 2.0 ** (retry_number - 1))
                from datetime import UTC, datetime, timedelta
                now = datetime.now(UTC)
                retry_at = now + timedelta(seconds=delay)
                telemetry = {"retry_number": retry_number, "attempt": job.attempt_count, "delay_seconds": delay, "error": str(exc), "recorded_at": now.isoformat()}
                self._update(job, status="retrying", error=str(exc), retry_count=retry_number, last_retry_delay_seconds=delay, next_retry_at=retry_at.isoformat(), retry_telemetry=[*job.retry_telemetry, telemetry])
                deadline = time.monotonic() + delay
                while time.monotonic() < deadline:
                    if self._cancel[job.job_id].is_set():
                        self._update(job, status="cancelled", error="download cancelled during retry backoff; partial files retained for resume", cancel_requested=False, next_retry_at=None)
                        return
                    if self._pause[job.job_id].is_set():
                        self._update(job, status="paused", error="download paused during retry backoff; partial files retained for resume", pause_requested=False, next_retry_at=None)
                        return
                    time.sleep(min(0.2, max(0.01, deadline - time.monotonic())))
                continue
            except Exception as exc:
                self._update(job, status="failed", error=str(exc), next_retry_at=None)
                return
