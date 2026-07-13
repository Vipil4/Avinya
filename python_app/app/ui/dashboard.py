from __future__ import annotations

import datetime as dt

import streamlit as st

from app.data import get_academic_calendar
from app.storage import StudentStore


def _next_exam_countdown() -> str:
    today = dt.date.today()
    events = get_academic_calendar()
    exam_dates = []
    for key, (kind, _label) in events.items():
        if kind != "ex":
            continue
        try:
            y, m, d = (int(p) for p in key.split("-"))
            exam_dates.append(dt.date(y, m + 1, d))  # stored month is 0-indexed
        except ValueError:
            continue
    upcoming = sorted(d for d in exam_dates if d >= today)
    if not upcoming:
        return "✅ No upcoming exams on the loaded calendar."
    days = (upcoming[0] - today).days
    if days == 0:
        return "🔴 EXAM TODAY! Check the Calendar tab."
    urgency = "⚠️ Final sprint — focus on weak areas now." if days <= 7 else "📚 Plan your study schedule."
    return f"{days} days until your next exam. {urgency}"


def render(store: StudentStore) -> None:
    profile = st.session_state["profile"]
    name = profile.get("name") or "Student"
    st.subheader(f"Welcome back, {name} 👋")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Notes saved", len(profile.get("notes", {})))
    with col2:
        st.metric("Quizzes completed", len(profile.get("mcq_history", [])))
    with col3:
        st.metric("Placement applications", len(profile.get("placements", [])))

    st.info(_next_exam_countdown())

    hist = profile.get("mcq_history", [])
    if hist:
        weakest = min(hist, key=lambda h: h.get("pct", 100))
        st.caption(f"Weakest recent topic: **{weakest.get('sub', '—')}** ({weakest.get('pct', 0)}%)")
    else:
        st.caption("Complete a quiz or add notes to start building your dashboard insights.")
