"""Minimal isolated worker protocol endpoint.

The process deliberately performs protocol validation only. Runtime-specific
model loading and inference are delegated to approved worker implementations.
"""
from __future__ import annotations

import sys
from pathlib import Path

from .worker_protocol import WorkerRequest, WorkerResponse, decode_message, encode_message


def handle_request(request: WorkerRequest) -> WorkerResponse:
    """Return a deterministic acknowledgement for an approved worker request."""
    if request.input_ref and not Path(request.input_ref).is_absolute():
        return WorkerResponse(request.request_id, "rejected", 2, ({"code": "input_path_not_absolute", "severity": "error"},))
    if request.output_ref and not Path(request.output_ref).is_absolute():
        return WorkerResponse(request.request_id, "rejected", 2, ({"code": "output_path_not_absolute", "severity": "error"},))
    return WorkerResponse(request.request_id, "accepted", 0, result={"operation": request.operation, "model_id": request.model_id, "model_checksum": request.model_checksum, "policy_id": request.policy_id})


def main() -> int:
    for line in sys.stdin.buffer:
        try:
            request = WorkerRequest.from_dict(decode_message(line))
            response = handle_request(request)
        except Exception as exc:  # protocol boundary must always produce a response
            response = WorkerResponse("", "rejected", 2, ({"code": "invalid_worker_request", "message": str(exc), "severity": "error"},))
        sys.stdout.buffer.write(encode_message(response.to_dict()))
        sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
