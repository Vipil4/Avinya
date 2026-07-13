"""Avinya (Python edition) — Streamlit entrypoint.

Run with: streamlit run main.py
"""
from __future__ import annotations

import streamlit as st

from config import settings
from app.llm.client import AnthropicClient
from app.storage import StudentStore
from app.ui import (
    ai_assist,
    calendar_tab,
    cases,
    dashboard,
    document_intel,
    faculty,
    major_advisor,
    placement_tracker,
    pomodoro,
    search_tab,
    study,
)

st.set_page_config(page_title="Avinya — IIT Roorkee eMBA Intelligence Platform", page_icon="🎓", layout="wide")

store = StudentStore()


def _init_session() -> None:
    if "student_id" not in st.session_state:
        st.session_state["student_id"] = "guest"
    if "profile" not in st.session_state:
        st.session_state["profile"] = store.load(st.session_state["student_id"])
    if "api_key_override" not in st.session_state:
        st.session_state["api_key_override"] = ""
    if "client" not in st.session_state or st.session_state.get("_client_key") != _effective_key():
        st.session_state["client"] = AnthropicClient(api_key=_effective_key())
        st.session_state["_client_key"] = _effective_key()


def _effective_key() -> str:
    return st.session_state.get("api_key_override") or settings.anthropic_api_key


def _render_sidebar() -> None:
    with st.sidebar:
        st.markdown("### 🎓 Avinya")
        st.caption("IIT Roorkee eMBA Intelligence Platform")

        new_id = st.text_input("Student / Roll number", value=st.session_state["student_id"])
        if new_id and new_id != st.session_state["student_id"]:
            st.session_state["student_id"] = new_id
            st.session_state["profile"] = store.load(new_id)
            st.rerun()

        st.divider()
        st.markdown("**Connect AI**")
        key_input = st.text_input(
            "Anthropic API key (sk-ant-...)", type="password", value=st.session_state["api_key_override"]
        )
        if st.button("Save key", use_container_width=True):
            st.session_state["api_key_override"] = key_input.strip()
            st.rerun()
        if st.session_state["client"].is_configured:
            st.success(f"✓ AI active ({st.session_state['client'].model})")
        else:
            st.info("No API key set — set ANTHROPIC_API_KEY as an env var, or paste one above.")


def main() -> None:
    _init_session()
    _render_sidebar()

    tabs = st.tabs(
        ["🏠 Home", "📚 Study", "📋 Cases", "🤖 AI Assist", "🎓 Major", "👤 Faculty", "📅 Calendar", "🔍 Search", "📌 Placements"]
    )
    with tabs[0]:
        dashboard.render(store)
    with tabs[1]:
        study.render(store)
        st.divider()
        pomodoro.render(store)
    with tabs[2]:
        cases.render(store)
    with tabs[3]:
        ai_assist.render(store)
        st.divider()
        document_intel.render(store)
    with tabs[4]:
        major_advisor.render(store)
    with tabs[5]:
        faculty.render(store)
    with tabs[6]:
        calendar_tab.render(store)
    with tabs[7]:
        search_tab.render(store)
    with tabs[8]:
        placement_tracker.render(store)


if __name__ == "__main__":
    main()
