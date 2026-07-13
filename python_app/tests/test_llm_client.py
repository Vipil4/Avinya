from unittest.mock import MagicMock

import anthropic
import httpx
import pytest

from app.llm.client import AnthropicClient


@pytest.fixture
def client():
    c = AnthropicClient(api_key="sk-ant-test-key", model="claude-sonnet-5")
    c._client = MagicMock()
    return c


def _fake_response(text="Hello from Claude"):
    resp = MagicMock()
    block = MagicMock()
    block.type = "text"
    block.text = text
    resp.content = [block]
    resp.usage.input_tokens = 12
    resp.usage.output_tokens = 34
    return resp


def test_complete_without_api_key_returns_error_not_exception():
    c = AnthropicClient(api_key="")
    result = c.complete(messages=[{"role": "user", "content": "hi"}])
    assert not result.ok
    assert "not configured" in result.error.lower()


def test_complete_success_extracts_text_and_usage(client):
    client._client.messages.create.return_value = _fake_response("Porter's Five Forces are...")
    result = client.complete(messages=[{"role": "user", "content": "explain"}], system="sys")
    assert result.ok
    assert result.text == "Porter's Five Forces are..."
    assert result.input_tokens == 12
    assert result.output_tokens == 34


def test_complete_handles_timeout_without_raising(client):
    client._client.messages.create.side_effect = anthropic.APITimeoutError(request=MagicMock())
    result = client.complete(messages=[{"role": "user", "content": "hi"}])
    assert not result.ok
    assert "timed out" in result.error.lower()


def test_complete_handles_api_status_error_without_raising(client):
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    response = httpx.Response(500, request=request, json={"error": {"message": "internal error"}})
    client._client.messages.create.side_effect = anthropic.APIStatusError(
        "500 error", response=response, body={"error": {"message": "internal error"}}
    )
    result = client.complete(messages=[{"role": "user", "content": "hi"}])
    assert not result.ok
    assert "500" in result.error


def test_complete_handles_connection_error_without_raising(client):
    client._client.messages.create.side_effect = anthropic.APIConnectionError(request=MagicMock())
    result = client.complete(messages=[{"role": "user", "content": "hi"}])
    assert not result.ok
    assert "connection error" in result.error.lower()


def test_complete_never_raises_on_unexpected_exception(client):
    client._client.messages.create.side_effect = RuntimeError("something weird")
    result = client.complete(messages=[{"role": "user", "content": "hi"}])
    assert not result.ok
    assert "unexpected error" in result.error.lower()
