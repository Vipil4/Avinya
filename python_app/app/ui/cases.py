from __future__ import annotations

import streamlit as st

from app.agents.orchestrator import Orchestrator
from app.llm.prompts import CASE_STYLE_LABELS, SYS_CASE_WRITER, build_case_study_prompt
from app.storage import StudentStore
from app.ui.components import require_api_key

_SUBJECTS = [
    "Operations Research", "Financial Management", "Marketing Management", "Strategic Management",
    "Organizational Behaviour", "Business Statistics", "Human Resource Management", "Data Science for Managers",
]
_INDUSTRIES = ["Indian Manufacturing", "IT & Technology", "Retail & E-commerce", "Banking & Finance", "Healthcare", "FMCG"]


def render(store: StudentStore) -> None:
    st.markdown("### 📋 Case Study Generator")
    profile = st.session_state["profile"]

    col1, col2, col3 = st.columns(3)
    with col1:
        subject = st.selectbox("Subject", _SUBJECTS)
    with col2:
        industry = st.selectbox("Industry", _INDUSTRIES)
    with col3:
        style = st.selectbox("Style", list(CASE_STYLE_LABELS.keys()), format_func=lambda k: CASE_STYLE_LABELS[k])

    if st.button("Generate case study", type="primary"):
        if require_api_key():
            orch = Orchestrator(st.session_state["client"])
            prompt = build_case_study_prompt(
                subject=subject,
                industry=industry,
                style=style,
                student_name=profile.get("name", "Student").split(" ")[0] if profile.get("name") else "Student",
                term=profile.get("term", "eMBA"),
                work=profile.get("work", "not specified"),
                goal=profile.get("goal", "senior management"),
            )
            with st.spinner("Claude is generating your case study..."):
                result = orch.answer(prompt, SYS_CASE_WRITER, web_search=False, max_tokens=3000)

            if result.ok:
                text = result.text
                title_line = next((l for l in text.splitlines() if l.strip().startswith("CASE TITLE:")), "")
                title = title_line.replace("CASE TITLE:", "").strip() or f"{subject} — {industry}"
                body = text.replace(title_line, "", 1).strip()
                st.markdown(f"#### 📋 {title}")
                st.markdown(body)
            else:
                st.error(f"Case generation failed: {result.error}")
