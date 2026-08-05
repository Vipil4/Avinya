from __future__ import annotations

import streamlit as st

from app.agents.orchestrator import Orchestrator
from app.llm.prompts import SYS_ASSIST
from app.storage import StudentStore
from app.ui.components import render_agent_trace, require_api_key, save_profile


def render(store: StudentStore) -> None:
    st.markdown("### 🤖 AI Assist")
    st.caption("Ask about any DoMS eMBA course, framework, or exam topic.")

    if "assist_history" not in st.session_state:
        st.session_state["assist_history"] = []

    for msg in st.session_state["assist_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("e.g. Explain Porter's Five Forces for Reliance Jio...")
    if prompt:
        st.session_state["assist_history"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        if require_api_key():
            orch = Orchestrator(st.session_state["client"])
            # last 10 turns of prior context, Anthropic message format
            history = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state["assist_history"][-11:-1]
            ]
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    result = orch.answer(prompt, SYS_ASSIST, history=history, web_search=True)
                if result.ok:
                    st.markdown(result.text)
                    render_agent_trace(result)
                    st.session_state["assist_history"].append({"role": "assistant", "content": result.text})

                    profile = st.session_state["profile"]
                    mem = profile.setdefault("memory_log", [])
                    mem.insert(0, {"type": "chat", "q": prompt[:80], "a": result.text[:200]})
                    profile["memory_log"] = mem[:100]
                    save_profile(store, st.session_state["student_id"])
                else:
                    st.error(result.error)
