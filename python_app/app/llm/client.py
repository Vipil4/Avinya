"""Thin wrapper around the Anthropic Python SDK.

Compared to the original app's fetch-based calls, this fixes a bug found
during testing: the original had *no* client-side request timeout, so a
hung backend left the UI spinning forever with no feedback. Every call
here goes through `_REQUEST_TIMEOUT_SECONDS`, and failures come back as a
normal `LLMResult(ok=False, ...)` rather than an unbounded wait or an
uncaught exception, so calling UI code can always render *something*.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

import anthropic

from config import settings

logger = logging.getLogger(__name__)

_REQUEST_TIMEOUT_SECONDS = 30.0
_WEB_SEARCH_TOOL = {"type": "web_search_20250305", "name": "web_search"}


@dataclass
class LLMResult:
    ok: bool
    text: str = ""
    error: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    used_web_search: bool = False
    used_mcp_servers: list[str] = field(default_factory=list)


class AnthropicClient:
    """One client per (api_key) — cheap to construct, safe to reuse."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or settings.anthropic_api_key
        self.model = model or settings.model
        self._client = anthropic.Anthropic(
            api_key=self.api_key, timeout=_REQUEST_TIMEOUT_SECONDS
        ) if self.api_key else None

    @property
    def is_configured(self) -> bool:
        return self._client is not None

    def complete(
        self,
        messages: list[dict],
        system: str = "",
        max_tokens: int | None = None,
        web_search: bool = False,
        mcp_server_urls: dict[str, str] | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> LLMResult:
        """`mcp_server_urls` is a {name: url} map of remote MCP connectors
        to attach (beta feature). If the SDK/account doesn't support it,
        we log and silently retry without MCP rather than failing the
        whole request — mirroring the original app's "attempt MCP, else
        fall back to web search" behaviour."""
        if not self.is_configured:
            return LLMResult(ok=False, error="AI not configured — no Anthropic API key set.")

        kwargs = dict(
            model=self.model,
            max_tokens=max_tokens or settings.max_tokens,
            messages=messages,
        )
        if system:
            kwargs["system"] = system
        if extra_headers:
            kwargs["extra_headers"] = extra_headers

        tools = [_WEB_SEARCH_TOOL] if web_search else None
        if tools:
            kwargs["tools"] = tools

        if mcp_server_urls:
            try:
                return self._complete_with_mcp(kwargs, mcp_server_urls)
            except Exception as e:  # noqa: BLE001 - deliberately broad: MCP is best-effort
                logger.warning("MCP connector call failed (%s); falling back to plain call.", e)

        return self._call(kwargs)

    def _complete_with_mcp(self, kwargs: dict, mcp_server_urls: dict[str, str]) -> LLMResult:
        mcp_servers = [
            {"type": "url", "url": url, "name": name} for name, url in mcp_server_urls.items()
        ]
        beta_kwargs = dict(kwargs)
        beta_kwargs["mcp_servers"] = mcp_servers
        resp = self._client.beta.messages.create(
            **beta_kwargs, extra_headers={"anthropic-beta": "mcp-client-2025-04-04"}
        )
        return self._to_result(resp, used_mcp_servers=list(mcp_server_urls.keys()))

    def _call(self, kwargs: dict) -> LLMResult:
        try:
            resp = self._client.messages.create(**kwargs)
            return self._to_result(resp, used_web_search=bool(kwargs.get("tools")))
        except anthropic.APITimeoutError:
            return LLMResult(ok=False, error="Request timed out. The AI backend may be slow — try again.")
        except anthropic.APIStatusError as e:
            return LLMResult(ok=False, error=f"API error ({e.status_code}): {_extract_message(e)}")
        except anthropic.APIConnectionError as e:
            return LLMResult(ok=False, error=f"Connection error: {e}")
        except Exception as e:  # noqa: BLE001 - last-resort guard, never let a call crash the UI
            logger.exception("Unexpected error calling Anthropic API")
            return LLMResult(ok=False, error=f"Unexpected error: {e}")

    @staticmethod
    def _to_result(resp, used_web_search: bool = False, used_mcp_servers: list[str] | None = None) -> LLMResult:
        text_parts = [block.text for block in resp.content if getattr(block, "type", None) == "text"]
        usage = getattr(resp, "usage", None)
        return LLMResult(
            ok=True,
            text="\n".join(text_parts) or "No response generated.",
            input_tokens=getattr(usage, "input_tokens", 0) or 0,
            output_tokens=getattr(usage, "output_tokens", 0) or 0,
            used_web_search=used_web_search,
            used_mcp_servers=used_mcp_servers or [],
        )


def _extract_message(e: "anthropic.APIStatusError") -> str:
    try:
        body = e.response.json()
        return body.get("error", {}).get("message", str(e))
    except Exception:  # noqa: BLE001
        return str(e)
