"""The orchestrator: classifies query intent into a set of named "agents"
(for UI display and MCP-connector selection), makes one grounded Claude
call with the right tools attached, and returns a trace the UI can render
as a live agent-activity panel — mirroring the original app's behaviour.
"""
from __future__ import annotations

import re
import time

from app.agents.base import AgentMeta, OrchestratorResult, TraceEvent
from app.llm.client import AnthropicClient
from app.mcp.registry import get_mcp_servers_for

AGENT_META: dict[str, AgentMeta] = {
    "orch": AgentMeta("orch", "Orchestrator", "🤖"),
    "iitr": AgentMeta("iitr", "IITR KB", "🏛"),
    "web": AgentMeta("web", "Web Search", "🌐"),
    "li": AgentMeta("li", "LinkedIn", "🔗"),
    "stat": AgentMeta("stat", "Statista", "📊"),
    "gs": AgentMeta("gs", "Scholar", "🎓"),
    "mospi": AgentMeta("mospi", "MoSPI", "🇮🇳"),
    "indeed": AgentMeta("indeed", "Indeed", "💼"),
    "cons": AgentMeta("cons", "Consensus", "📝"),
    "mstar": AgentMeta("mstar", "Morningstar", "⭐"),
    "dw": AgentMeta("dw", "Deep Web", "🔎"),
}

# agent key -> MCP registry key, for the agents that map to a real remote
# connector. Agents without an entry here (li, stat, dw) fall back to the
# web_search tool, same as the original.
_AGENT_TO_MCP_KEY = {
    "mospi": "mospi",
    "indeed": "indeed",
    "cons": "consensus",
    "mstar": "morningstar",
}

_INTENT_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("li", re.compile(r"linkedin|job|career|professor|faculty|phd|qualification", re.I)),
    ("mospi", re.compile(r"india|gdp|economy|mospi", re.I)),
    ("cons", re.compile(r"paper|research|study|journal", re.I)),
    ("mstar", re.compile(r"stock|equity|fund|market cap", re.I)),
    ("stat", re.compile(r"stat|data|percent|growth rate", re.I)),
    ("indeed", re.compile(r"placement|hiring|recruiter|salary package", re.I)),
]


def classify_intent(query: str) -> list[str]:
    """Always includes orch + iitr (the grounding KB); adds any matched
    specialist agents on top, same heuristic the original used."""
    active = ["orch", "iitr"]
    for agent_key, pattern in _INTENT_PATTERNS:
        if pattern.search(query or "") and agent_key not in active:
            active.append(agent_key)
    return active


class Orchestrator:
    def __init__(self, client: AnthropicClient):
        self.client = client

    def answer(
        self,
        query: str,
        system_prompt: str,
        history: list[dict] | None = None,
        web_search: bool = True,
        max_tokens: int | None = None,
    ) -> OrchestratorResult:
        t0 = time.time()
        active_agents = classify_intent(query)
        trace = [TraceEvent("orch", f"Query received: {query[:80]}", "start")]
        trace.append(TraceEvent("iitr", "Loading DoMS IITR curriculum & faculty context", "info"))
        trace.append(TraceEvent("orch", "Applying quality standards & anti-hallucination guards", "quality"))

        mcp_keys = [_AGENT_TO_MCP_KEY[a] for a in active_agents if a in _AGENT_TO_MCP_KEY]
        mcp_urls = get_mcp_servers_for(mcp_keys) if mcp_keys and self.client.api_key.startswith("sk-ant") else {}
        if mcp_urls:
            trace.append(TraceEvent("orch", f"Attaching MCP connectors: {', '.join(mcp_urls)}", "info"))

        messages = list(history or [])
        messages.append({"role": "user", "content": query})

        result = self.client.complete(
            messages=messages,
            system=system_prompt,
            max_tokens=max_tokens,
            web_search=web_search and not mcp_urls,
            mcp_server_urls=mcp_urls or None,
        )
        elapsed = time.time() - t0

        if not result.ok:
            trace.append(TraceEvent("orch", f"Failed: {result.error}", "result"))
            return OrchestratorResult(
                ok=False,
                text="",
                error=result.error,
                active_agents=active_agents,
                trace=trace,
                elapsed_seconds=elapsed,
            )

        trace.append(TraceEvent("orch", f"Done in {elapsed:.1f}s", "result"))
        return OrchestratorResult(
            ok=True,
            text=result.text,
            active_agents=active_agents,
            trace=trace,
            elapsed_seconds=elapsed,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
        )
