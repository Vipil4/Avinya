from __future__ import annotations

import streamlit as st

from app.agents.orchestrator import Orchestrator
from app.llm.prompts import SYS_MAJOR, build_major_advisor_prompt
from app.storage import StudentStore
from app.ui.components import render_agent_trace, require_api_key, save_profile

_SPECIALIZATIONS = ["Operations", "Finance", "Marketing", "Information Systems", "HR"]


def render(store: StudentStore) -> None:
    st.markdown("### 🎓 Major Advisor")
    profile = st.session_state["profile"]

    terms = ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8"]
    with st.form("major_profile_form"):
        name = st.text_input("Name", value=profile.get("name", ""))
        term = st.selectbox(
            "Current term", terms, index=terms.index(profile.get("term")) if profile.get("term") in terms else 0
        )
        work = st.text_input("Work background", value=profile.get("work", ""))
        goal = st.text_input("Career goal", value=profile.get("goal", ""))
        submitted = st.form_submit_button("Get my specialization recommendation")

    if submitted:
        profile.update({"name": name, "term": term, "work": work, "goal": goal})
        save_profile(store, st.session_state["student_id"])

        if require_api_key():
            orch = Orchestrator(st.session_state["client"])
            with st.spinner("Analysing your profile..."):
                result = orch.answer(build_major_advisor_prompt(profile), SYS_MAJOR, web_search=False)
            if result.ok:
                st.markdown(f"**Based on:** {name or 'your profile'}" + (f"  ·  Goal: {goal}" if goal else ""))
                st.markdown(result.text)
                render_agent_trace(result)
            else:
                st.error(result.error)

    st.divider()
    st.caption("The 5 DoMS IITR specialisation tracks:")
    st.write(" · ".join(_SPECIALIZATIONS))
