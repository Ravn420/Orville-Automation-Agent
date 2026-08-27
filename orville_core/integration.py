"""Adapters that connect provider routing to the orchestration engine."""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Iterator

from .agent_contracts import StreamPolicy
from .models import TaskNode
from .providers import LLMRequest, ProviderError
from .sandbox_adapters import discover_sandbox_adapters
from .routing import ProviderRouter, RoutingRequest
from .workflow import VerificationRecord


def _require_sandbox_if_requested(inputs: dict[str, Any], context: dict[str, Any]) -> None:
    """Fail closed when a task requires isolation but no adapter is available."""

    if not bool(inputs.get("requires_sandbox", False)):
        return
    requested = str(inputs.get("sandbox_adapter", "auto"))
    adapters = context.get("_sandbox_adapters") or discover_sandbox_adapters()
    candidates = adapters.values() if requested == "auto" else (adapters.get(requested),)
    if not any(adapter is not None and adapter.available() for adapter in candidates):
        raise ProviderError(f"sandbox_unavailable: no approved adapter is available for requested sandbox '{requested}'")


def model_task_handler(router: ProviderRouter):
    """Return an engine handler that executes a task through ProviderRouter.

    Task inputs may contain ``messages`` and the optional routing keys
    ``required_capabilities``, ``preferred_provider_ids``, ``local_only``, and
    ``allow_fallback``. Routing metadata is returned with the task output so it
    is persisted by the engine in the normal checkpoint context.
    """

    def handle(task: TaskNode, context: dict[str, Any]) -> dict[str, Any]:
        inputs = task.inputs
        _require_sandbox_if_requested(inputs, context)
        messages = inputs.get("messages")
        if not messages:
            prompt = inputs.get("prompt") or inputs.get("objective")
            if not prompt:
                raise ValueError(f"model task {task.task_id} requires messages, prompt, or objective")
            messages = [{"role": "user", "content": prompt}]
        routing = RoutingRequest(
            required_capabilities=frozenset(inputs.get("required_capabilities", ["text"])),
            preferred_provider_ids=tuple(inputs.get("preferred_provider_ids", [])),
            local_only=bool(inputs.get("local_only", False)),
            allow_fallback=bool(inputs.get("allow_fallback", True)),
            privacy_class=inputs.get("privacy_class"),
        )
        request = LLMRequest(messages=messages, temperature=inputs.get("temperature"), max_tokens=inputs.get("max_tokens"), response_schema=inputs.get("response_schema"), tools=inputs.get("tools", []))
        response, route = router.generate(request, routing)
        return {
            "text": response.text,
            "provider_id": response.provider_id,
            "model": response.model,
            "finish_reason": response.finish_reason,
            "tool_calls": [{"name": call.name, "arguments": call.arguments} for call in response.tool_calls],
            "usage": response.usage,
            "routing": {"selected_provider": route.provider_id, "attempts": [attempt.__dict__ for attempt in route.attempts]},
        }

    return handle


def streaming_model_task_handler(router: ProviderRouter):
    """Return a model handler that streams incremental output into run events.

    The engine supplies a transient ``_progress_callback`` in the execution
    context. It is never persisted; only the emitted event records and the
    final output are durable.
    """

    def handle(task: TaskNode, context: dict[str, Any]) -> dict[str, Any]:
        inputs = task.inputs
        _require_sandbox_if_requested(inputs, context)
        messages = inputs.get("messages")
        if not messages:
            prompt = inputs.get("prompt") or inputs.get("objective")
            if not prompt:
                raise ValueError(f"model task {task.task_id} requires messages, prompt, or objective")
            messages = [{"role": "user", "content": prompt}]
        routing = RoutingRequest(
            required_capabilities=frozenset(inputs.get("required_capabilities", ["text", "streaming"])),
            preferred_provider_ids=tuple(inputs.get("preferred_provider_ids", [])),
            local_only=bool(inputs.get("local_only", False)),
            allow_fallback=bool(inputs.get("allow_fallback", True)),
            privacy_class=inputs.get("privacy_class"),
        )
        request = LLMRequest(messages=messages, temperature=inputs.get("temperature"), max_tokens=inputs.get("max_tokens"), response_schema=inputs.get("response_schema"), tools=inputs.get("tools", []))
        progress = context.get("_progress_callback")
        partial_checkpoint = context.get("_partial_checkpoint_callback")
        policy = StreamPolicy(**inputs.get("stream_policy", {}))
        resume_text = str(inputs.get("resume_text", ""))
        parts: list[str] = [resume_text] if resume_text else []
        chunk_count = 0
        provider_id = ""
        model = ""
        finish_reason = None
        usage: dict[str, int] = {}
        tool_calls: list[dict[str, Any]] = []
        def resumable_stream() -> Iterator[Any]:
            attempts = 0
            replay_skip = len(resume_text)
            while True:
                try:
                    for next_chunk in router.stream(request, routing):
                        if replay_skip and next_chunk.text:
                            if len(next_chunk.text) <= replay_skip:
                                replay_skip -= len(next_chunk.text)
                                next_chunk = replace(next_chunk, text="")
                            else:
                                next_chunk = replace(next_chunk, text=next_chunk.text[replay_skip:])
                                replay_skip = len(resume_text)
                        yield next_chunk
                    return
                except ProviderError:
                    if attempts >= policy.reconnect_attempts:
                        raise
                    attempts += 1
                    replay_skip = len("".join(parts))
                    if partial_checkpoint and policy.preserve_partial_output:
                        partial_checkpoint({"text": "".join(parts), "provider_id": provider_id, "model": model, "chunks": chunk_count, "partial": True, "reconnect_attempt": attempts})
                    if progress:
                        progress("model_stream_reconnected", {"attempt": attempts, "chunks": chunk_count, "text": "".join(parts)})

        for chunk in resumable_stream():
            chunk_count += 1
            if context.get(policy.cancellation_key):
                if partial_checkpoint and policy.preserve_partial_output:
                    partial_checkpoint({"text": "".join(parts), "provider_id": provider_id, "model": model, "chunks": chunk_count, "partial": True, "cancelled": True})
                if progress:
                    progress("model_stream_cancelled", {"text": "".join(parts), "chunks": chunk_count})
                return {"text": "".join(parts), "provider_id": provider_id, "model": model, "finish_reason": "cancelled", "tool_calls": tool_calls, "usage": usage, "streamed": True, "partial": True}
            provider_id = chunk.provider_id
            model = chunk.model
            finish_reason = chunk.finish_reason or finish_reason
            usage.update(chunk.usage)
            if chunk.tool_calls:
                tool_calls.extend({"name": call.name, "arguments": call.arguments} for call in chunk.tool_calls)
            if chunk.text:
                parts.append(chunk.text)
                text = "".join(parts)
                if len(text) > policy.max_buffer_chars:
                    raise ProviderError(f"stream output exceeded max_buffer_chars ({policy.max_buffer_chars})")
                if progress:
                    progress("model_output_delta", {"delta": chunk.text, "text": text, "provider_id": provider_id, "model": model})
                if partial_checkpoint and chunk_count % policy.checkpoint_every_chunks == 0 and policy.preserve_partial_output:
                    partial_checkpoint({"text": text, "provider_id": provider_id, "model": model, "chunks": chunk_count, "partial": True})
        return {
            "text": "".join(parts),
            "provider_id": provider_id,
            "model": model,
            "finish_reason": finish_reason,
            "tool_calls": tool_calls,
            "usage": usage,
            "streamed": True,
            "resumed_from_partial": bool(resume_text),
        }

    return handle


def verify_output(task_id: str, output: Any, *, verifier_agent: str = "verification", criteria: list[str] | None = None) -> VerificationRecord:
    """Perform a minimal deterministic output gate for model-backed tasks."""
    checks = []
    if isinstance(output, dict) and isinstance(output.get("text"), str) and output["text"].strip():
        checks.append({"name": "non_empty_text", "passed": True})
    else:
        checks.append({"name": "non_empty_text", "passed": False})
    if criteria:
        text = output.get("text", "") if isinstance(output, dict) else str(output)
        for criterion in criteria:
            passed = criterion.lower() in text.lower()
            checks.append({"name": "criterion", "criterion": criterion, "passed": passed})
    passed = all(check["passed"] for check in checks)
    defects = tuple(check.get("criterion", check["name"]) for check in checks if not check["passed"])
    return VerificationRecord(f"verification:{task_id}", task_id, verifier_agent, passed, tuple(checks), defects, ())



