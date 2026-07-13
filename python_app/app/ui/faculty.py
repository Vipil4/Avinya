from __future__ import annotations

import streamlit as st

from app.agents.orchestrator import Orchestrator
from app.data import search_faculty
from app.llm.prompts import SYS_FACULTY_PROFILER
from app.storage import StudentStore
from app.ui.components import require_api_key

_AREA_LABELS = {
    "all": "All",
    "ops": "Operations",
    "fin": "Finance",
    "mkt": "Marketing",
    "hr": "HR",
    "is": "Info Systems",
    "practice": "Professors of Practice",
    "retired": "Retired",
}


def render(store: StudentStore) -> None:
    st.markdown("### 👤 Faculty Directory")
    col1, col2 = st.columns([2, 1])
    with col1:
        query = st.text_input("Search by name, research area, subject...", key="fac_search")
    with col2:
        area = st.selectbox("Filter", list(_AREA_LABELS.keys()), format_func=lambda k: _AREA_LABELS[k], key="fac_area")

    results = search_faculty(query, area)
    st.caption(f"{len(results)} faculty found")

    for f in results:
        with st.expander(f"{f.name} — {f.role}"):
            st.write(f"**Research:** {f.research}")
            st.write(f"📧 {f.email}  ·  📞 {f.phone}  ·  📍 {f.room}")
            st.markdown(f"[IITR profile]({f.profile_url})")

            if st.button("✦ AI-enhanced profile (web search)", key=f"enhance_{f.name}"):
                if require_api_key():
                    orch = Orchestrator(st.session_state["client"])
                    query_text = (
                        f"Find publicly available professional background for {f.name}, "
                        f"{f.role} at IIT Roorkee DoMS. Cover education (PhD/MTech institution and year), "
                        "prior industry/academic experience, and notable publications. "
                        "150 words max. Note the data source."
                    )
                    with st.spinner("Searching..."):
                        result = orch.answer(query_text, SYS_FACULTY_PROFILER, web_search=True)
                    if result.ok:
                        st.markdown(result.text)
                    else:
                        st.error(result.error)
