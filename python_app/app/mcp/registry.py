"""Registry of remote MCP connectors Avinya can attach to a Claude call.

These mirror the original app's MCP_SERVERS map (mospi.gov.in for Indian
official statistics, Indeed for live job search, Consensus for academic
papers, Morningstar for financial data). Remote MCP connectors are only
usable in direct-API-key mode (the Anthropic Messages API `mcp_servers`
beta parameter needs Anthropic to reach the connector on your behalf);
when no MCP servers are wired up, callers should fall back to the
`web_search` tool, same as the original.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.data.loader import get_mcp_servers


@dataclass(frozen=True)
class MCPServerMeta:
    key: str
    label: str
    icon: str
    url: str


MCP_SERVER_META: dict[str, MCPServerMeta] = {
    "mospi": MCPServerMeta("mospi", "MoSPI (India stats)", "🇮🇳", ""),
    "indeed": MCPServerMeta("indeed", "Indeed (jobs)", "💼", ""),
    "consensus": MCPServerMeta("consensus", "Consensus (papers)", "📝", ""),
    "morningstar": MCPServerMeta("morningstar", "Morningstar (finance)", "⭐", ""),
}


def _hydrate() -> dict[str, MCPServerMeta]:
    urls = get_mcp_servers()
    out = {}
    for key, meta in MCP_SERVER_META.items():
        out[key] = MCPServerMeta(meta.key, meta.label, meta.icon, urls.get(key, ""))
    return out


def get_mcp_server_url(key: str) -> str:
    return _hydrate().get(key, MCPServerMeta(key, key, "🔌", "")).url


def get_mcp_servers_for(keys: list[str]) -> dict[str, str]:
    """Returns a {name: url} map suitable for AnthropicClient.complete(mcp_server_urls=...)."""
    hydrated = _hydrate()
    return {k: hydrated[k].url for k in keys if k in hydrated and hydrated[k].url}
