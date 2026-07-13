from __future__ import annotations

import streamlit as st

from app.agents.orchestrator import Orchestrator
from app.llm.prompts import SYS_SEARCH
from app.storage import StudentStore
from app.ui.components import render_agent_trace, require_api_key


def render(store: StudentStore) -> None:
    st.markdown("### 🔍 Live Search")
    st.caption("Ask about IIT Roorkee, eMBA curriculum, faculty, admissions, placements — with live web search.")

    if "search_history" not in st.session_state:
        st.session_state["search_history"] = []

    for msg in st.session_state["search_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("Search...")
    if prompt:
        st.session_state["search_history"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        if require_api_key():
            orch = Orchestrator(st.session_state["client"])
            history = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state["search_history"][-11:-1]
            ]
            with st.chat_message("assistant"):
                with st.spinner("Searching..."):
                    result = orch.answer(prompt, SYS_SEARCH, history=history, web_search=True)
                if result.ok:
                    st.markdown(result.text)
                    render_agent_trace(result)
                    st.session_state["search_history"].append({"role": "assistant", "content": result.text})
                else:
                    st.error(result.error)
