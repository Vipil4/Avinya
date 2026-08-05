"""Shared Streamlit widgets used across pages.

Note on the original app's stored-XSS bug: that bug existed because raw
LLM output was injected into the page via innerHTML with no escaping.
Streamlit's st.markdown/st.write never render HTML unless you pass
unsafe_allow_html=True — so as a hard rule, nothing in this module (or
any page module) passes unsafe_allow_html=True with LLM- or user-derived
text. Where we do use unsafe_allow_html for static styling, only
hardcoded strings go through it.
"""
from __future__ import annotations

import streamlit as st

from app.agents.base import OrchestratorResult
from app.agents.orchestrator import AGENT_META
from app.storage import ConflictError, StudentStore


def render_agent_trace(result: OrchestratorResult) -> None:
    if not result.active_agents:
        return
    pills = " ".join(
        f"{AGENT_META[a].icon} {AGENT_META[a].label}" for a in result.active_agents if a in AGENT_META
    )
    st.caption(f"Agents: {pills}  ·  {result.elapsed_seconds:.1f}s")
    with st.expander("Show reasoning trace", expanded=False):
        for ev in result.trace:
            meta = AGENT_META.get(ev.agent_key)
            icon = meta.icon if meta else "•"
            st.text(f"{icon} [{ev.agent_key}] {ev.message}")


def quality_badge(text: str) -> str:
    is_web_sourced = any(
        kw in (text or "").lower() for kw in ("source", "cited", "according to", "report", "http")
    )
    return "🔍 Web-sourced · verify independently" if is_web_sourced else "🤖 AI-generated · cross-check key facts"


def require_api_key() -> bool:
    if not st.session_state.get("client") or not st.session_state["client"].is_configured:
        st.warning("Connect your Anthropic API key in the sidebar to use AI features.")
        return False
    return True


def save_profile(store: StudentStore, student_id: str) -> None:
    """Persists st.session_state['profile'] back to disk, handling the
    same cross-tab conflict the original app silently lost data to."""
    profile = st.session_state["profile"]
    try:
        saved = store.save(student_id, profile, expected_version=profile.get("_version"))
        st.session_state["profile"] = saved
    except ConflictError:
        st.toast(
            "⚠️ This profile changed in another tab/session. Reloading the latest version — "
            "please redo your last change if needed.",
            icon="⚠️",
        )
        st.session_state["profile"] = store.load(student_id)
