from __future__ import annotations

import streamlit as st

from app.data import get_courses, search_courses, search_formulas
from app.storage import StudentStore
from app.ui.components import save_profile


def _render_course_notes(store: StudentStore) -> None:
    st.markdown("#### 📝 Course Notes")
    courses = get_courses()
    options = ["general"] + [c.code for c in courses]
    labels = {"general": "📋 General Notes"} | {c.code: f"{c.term} · {c.name}" for c in courses}

    course_key = st.selectbox(
        "Course", options=options, format_func=lambda k: labels.get(k, k), key="notes_course_sel"
    )

    profile = st.session_state["profile"]
    notes = profile.setdefault("notes", {})
    current_text = notes.get(course_key, "")

    text = st.text_area(
        "Type your notes here — auto-saved as you type.",
        value=current_text,
        height=280,
        key=f"note_editor_{course_key}",
    )
    if text != current_text:
        notes[course_key] = text
        save_profile(store, st.session_state["student_id"])
        st.caption("Saved ✓")


def _render_course_browser() -> None:
    st.markdown("#### 📖 Course Knowledge Base — Terms 1-7")
    query = st.text_input("Search by course, professor, or topic...", key="course_search")
    matches = search_courses(query)[:8]
    if not matches:
        st.caption("No matching courses found.")
    for c in matches:
        with st.expander(f"{c.name}  ·  {c.term}  ·  {c.professor}"):
            st.write(f"**Code:** {c.code}")
            if c.topics:
                st.write("**Topics:** " + " · ".join(c.topics[:6]))
            if c.frameworks:
                st.write("**Frameworks:** " + " · ".join(c.frameworks[:5]))


def _render_formula_reference() -> None:
    st.markdown("#### 📐 Formula Quick Reference")
    col1, col2 = st.columns([2, 1])
    with col1:
        query = st.text_input("Search formulas...", key="formula_search")
    with col2:
        categories = sorted({f.category for f in search_formulas()})
        category = st.selectbox("Category", ["all"] + categories, key="formula_category")

    for f in search_formulas(query, category)[:20]:
        st.markdown(f"**{f.name}** ({f.category})")
        st.code(f.formula, language=None)
        if f.description:
            st.caption(f.description)


def render(store: StudentStore) -> None:
    st.markdown("### 📚 Study")
    tab_notes, tab_browse, tab_formulas = st.tabs(["Notes", "Course Browser", "Formula Reference"])
    with tab_notes:
        _render_course_notes(store)
    with tab_browse:
        _render_course_browser()
    with tab_formulas:
        _render_formula_reference()
