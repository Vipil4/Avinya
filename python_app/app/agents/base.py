"""Shared types for the agent layer.

Architecture note: in the original app, the 11 "agents" shown in the UI
(Orchestrator, IITR KB, Web Search, LinkedIn, Statista, Scholar, MoSPI,
Indeed, Consensus, Morningstar, Deep Web) were not independent agentic
loops — they were a classification + attribution layer over a *single*
Claude call whose system prompt and tool/MCP selection changed based on
keyword-matched query intent. This rewrite keeps that same honest
architecture (it's simpler, cheaper, and was already working) rather than
pretending to add autonomous multi-agent loops the original never had.
`Orchestrator.answer()` is the one place that actually talks to the model;
everything else here is classification and UI-trace bookkeeping.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass(frozen=True)
class AgentMeta:
    key: str
    label: str
    icon: str


@dataclass
class TraceEvent:
    agent_key: str
    message: str
    kind: str  # 'start' | 'info' | 'quality' | 'result'
    ts: float = field(default_factory=time.time)


@dataclass
class OrchestratorResult:
    ok: bool
    text: str
    error: str = ""
    active_agents: list[str] = field(default_factory=list)
    trace: list[TraceEvent] = field(default_factory=list)
    elapsed_seconds: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
