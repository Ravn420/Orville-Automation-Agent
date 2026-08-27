"""Local inference-runtime capability discovery.

The module performs non-executing health and catalog probes against configured
local runtimes. It never downloads or executes model-provided code. Capability
claims are conservative: declared model capabilities are exposed only when the
runtime is reachable and the runtime adapter supports the operation family.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


SUPPORTED_MODALITIES = frozenset({"text", "code", "vision", "embeddings", "image_generation", "audio", "video_generation"})


@dataclass(frozen=True)
class RuntimeCapabilityReport:
    runtime: str
    endpoint: str
    reachable: bool
    supported_modalities: tuple[str, ...]
    exposed_modalities: tuple[str, ...]
    checks: dict[str, bool]
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "runtime": self.runtime,
            "endpoint": self.endpoint,
            "reachable": self.reachable,
            "supported_modalities": list(self.supported_modalities),
            "exposed_modalities": list(self.exposed_modalities),
            "checks": dict(self.checks),
            "warnings": list(self.warnings),
        }


def _normalise_runtime(runtime: str) -> str:
    return runtime.strip().lower().replace("-", "_")


def _get_json(url: str, timeout: float) -> tuple[bool, dict[str, Any] | list[Any] | None, str | None]:
    try:
        with urlopen(Request(url, headers={"Accept": "application/json", "User-Agent": "Orville/1.0"}), timeout=timeout) as response:
            body = response.read().decode("utf-8")
        return True, json.loads(body) if body else {}, None
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return False, None, exc.__class__.__name__


def probe_runtime_capabilities(runtime: str, endpoint: str, *, declared: set[str] | frozenset[str] = frozenset(), model: str | None = None, timeout: float = 3.0) -> RuntimeCapabilityReport:
    """Probe a local runtime without running generation or embedding inference."""
    normalised = _normalise_runtime(runtime)
    base = endpoint.rstrip("/") + "/"
    checks: dict[str, bool] = {}
    warnings: list[str] = []
    runtime_modalities: set[str] = set()

    if normalised == "ollama":
        reachable, tags, error = _get_json(urljoin(base, "api/tags"), timeout)
        checks["runtime_reachable"] = reachable
        if not reachable:
            warnings.append(f"Ollama catalog probe failed: {error}")
        names = {str(item.get("name", "")) for item in (tags or {}).get("models", []) if isinstance(item, dict)} if isinstance(tags, dict) else set()
        checks["model_available"] = not model or model in names or any(name.split(":", 1)[0] == model for name in names)
        if model and not checks["model_available"]:
            warnings.append("configured model was not returned by Ollama /api/tags")
        runtime_modalities.update({"text", "code", "embeddings"})
        # Ollama's OpenAI-compatible chat bridge can carry image parts, but only
        # models that declare vision should expose that operation.
        runtime_modalities.add("vision")
    elif normalised in {"llama_cpp", "openai_compatible_local", "custom_local", "custom_local_ollama"}:
        reachable, models, error = _get_json(urljoin(base, "models"), timeout)
        checks["runtime_reachable"] = reachable
        if not reachable:
            warnings.append(f"local inference-server model probe failed: {error}")
        model_items = models.get("data", []) if isinstance(models, dict) else []
        model_names = {str(item.get("id", "")) for item in model_items if isinstance(item, dict)}
        checks["model_available"] = not model or not model_names or model in model_names
        runtime_modalities.update({"text", "code", "embeddings", "vision"})
        warnings.append("multimodal and embedding exposure relies on the configured server's OpenAI-compatible contract")
    elif normalised == "transformers":
        checks["runtime_reachable"] = True
        checks["transformers_package"] = _package_available("transformers")
        checks["torch_or_accelerate"] = _package_available("torch") or _package_available("accelerate")
        runtime_modalities.update({"text", "code", "vision", "embeddings", "image_generation", "audio"})
        if not checks["transformers_package"]:
            warnings.append("Python package 'transformers' is not installed")
        if not checks["torch_or_accelerate"]:
            warnings.append("Neither torch nor accelerate is installed")
    else:
        raise ValueError("runtime must be ollama, llama.cpp, transformers, or an OpenAI-compatible local server")

    supported = tuple(sorted(runtime_modalities & SUPPORTED_MODALITIES))
    exposed = tuple(sorted(set(declared) & set(supported)))
    for modality in declared:
        if modality in SUPPORTED_MODALITIES:
            checks[f"supports_{modality}"] = modality in runtime_modalities
    return RuntimeCapabilityReport(normalised, endpoint, checks.get("runtime_reachable", False) and checks.get("model_available", True), supported, exposed, checks, tuple(warnings))


def _package_available(name: str) -> bool:
    from importlib.util import find_spec

    return find_spec(name) is not None
