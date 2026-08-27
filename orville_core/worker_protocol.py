"""Versioned JSON-lines protocol for isolated local-model workers."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Mapping

PROTOCOL_VERSION = 1
MAX_MESSAGE_BYTES = 1 * 1024 * 1024


@dataclass(frozen=True)
class WorkerRequest:
    request_id: str
    operation: str
    model_id: str
    model_checksum: str
    policy_id: str
    input_ref: str | None = None
    output_ref: str | None = None
    parameters: Mapping[str, Any] = field(default_factory=dict)
    protocol_version: int = PROTOCOL_VERSION

    def validate(self) -> None:
        if self.protocol_version != PROTOCOL_VERSION:
            raise ValueError("unsupported worker protocol version")
        if not self.request_id or not self.model_id or not self.model_checksum or not self.policy_id:
            raise ValueError("request_id, model_id, model_checksum, and policy_id are required")
        if self.operation not in {"inspect", "convert", "load", "infer", "embed"}:
            raise ValueError("unsupported worker operation")
        for value in (self.input_ref, self.output_ref):
            if value is not None and ("\x00" in value or not value):
                raise ValueError("worker references must be non-empty and NUL-free")

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "WorkerRequest":
        result = cls(
            request_id=str(payload.get("request_id", "")),
            operation=str(payload.get("operation", "")),
            model_id=str(payload.get("model_id", "")),
            model_checksum=str(payload.get("model_checksum", "")),
            policy_id=str(payload.get("policy_id", "")),
            input_ref=str(payload["input_ref"]) if payload.get("input_ref") is not None else None,
            output_ref=str(payload["output_ref"]) if payload.get("output_ref") is not None else None,
            parameters=dict(payload.get("parameters", {})),
            protocol_version=int(payload.get("protocol_version", 0)),
        )
        result.validate()
        return result

    def to_dict(self) -> dict[str, Any]:
        return {"protocol_version": self.protocol_version, "request_id": self.request_id, "operation": self.operation, "model_id": self.model_id, "model_checksum": self.model_checksum, "policy_id": self.policy_id, "input_ref": self.input_ref, "output_ref": self.output_ref, "parameters": dict(self.parameters)}


@dataclass(frozen=True)
class WorkerResponse:
    request_id: str
    status: str
    exit_code: int = 0
    diagnostics: tuple[dict[str, Any], ...] = ()
    result: Mapping[str, Any] = field(default_factory=dict)
    protocol_version: int = PROTOCOL_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {"protocol_version": self.protocol_version, "request_id": self.request_id, "status": self.status, "exit_code": self.exit_code, "diagnostics": list(self.diagnostics), "result": dict(self.result)}


def encode_message(payload: Mapping[str, Any]) -> bytes:
    encoded = (json.dumps(dict(payload), sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    if len(encoded) > MAX_MESSAGE_BYTES:
        raise ValueError("worker message exceeds size limit")
    return encoded


def decode_message(line: bytes | str) -> dict[str, Any]:
    raw = line.encode("utf-8") if isinstance(line, str) else line
    if len(raw) > MAX_MESSAGE_BYTES:
        raise ValueError("worker message exceeds size limit")
    payload = json.loads(raw.decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("worker message must be a JSON object")
    return payload
