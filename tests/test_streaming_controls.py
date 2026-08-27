import pytest

from orville_core import ProviderRegistry, ProviderRouter, ProviderConfig, ModelCapabilities, LLMResponse, StreamChunk
from orville_core.integration import streaming_model_task_handler
from orville_core.providers import ProviderError


class StreamingProvider:
    def __init__(self):
        self.config = ProviderConfig("stream", "test", "model", "https://example.test", capabilities=ModelCapabilities(streaming=True))

    def generate(self, request):
        return LLMResponse("stream", "model", "", {})

    def stream(self, request):
        yield StreamChunk("stream", "model", "one")
        yield StreamChunk("stream", "model", "two")
        yield StreamChunk("stream", "model", "three", finish_reason="stop")

    def embed(self, inputs):
        raise NotImplementedError

    def health_check(self):
        return {"ok": True}


def handler():
    registry = ProviderRegistry()
    registry.register(StreamingProvider())
    return streaming_model_task_handler(ProviderRouter(registry))


def task(policy=None):
    inputs = {"prompt": "hello", "preferred_provider_ids": ["stream"], "required_capabilities": ["text", "streaming"]}
    if policy:
        inputs["stream_policy"] = policy
    return type("Task", (), {"task_id": "stream-task", "inputs": inputs})()


def test_streaming_handler_checkpoints_partial_output_and_completes():
    checkpoints = []
    result = handler()(task({"checkpoint_every_chunks": 2}), {"_partial_checkpoint_callback": checkpoints.append})
    assert result["text"] == "onetwothree"
    assert checkpoints[0]["text"] == "onetwo"
    assert checkpoints[0]["partial"] is True


def test_streaming_handler_honors_cooperative_cancellation():
    events = []
    result = handler()(task(), {"cancel_requested": True, "_progress_callback": lambda event, details: events.append(event)})
    assert result["partial"] is True
    assert result["finish_reason"] == "cancelled"
    assert "model_stream_cancelled" in events


def test_streaming_handler_enforces_bounded_buffer():
    with pytest.raises(ProviderError, match="max_buffer_chars"):
        handler()(task({"max_buffer_chars": 5}), {})
