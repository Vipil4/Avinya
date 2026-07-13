from __future__ import annotations

import datetime as dt

import streamlit as st

from app.data import get_academic_calendar
from app.storage import StudentStore

_KIND_LABEL = {"cl": "🟢 Class", "ex": "🔴 Exam"}


def render(store: StudentStore) -> None:
    st.markdown("### 📅 Academic Calendar")

    events = get_academic_calendar()
    parsed = []
    for key, (kind, label) in events.items():
        try:
            y, m, d = (int(p) for p in key.split("-"))
            parsed.append((dt.date(y, m + 1, d), kind, label))
        except ValueError:
            continue
    parsed.sort(key=lambda t: t[0])

    show_past = st.checkbox("Show past events", value=False)
    today = dt.date.today()

    for date_, kind, label in parsed:
        if not show_past and date_ < today:
            continue
        badge = _KIND_LABEL.get(kind, kind)
        highlight = " **(TODAY)**" if date_ == today else ""
        st.write(f"{badge}  ·  {date_.strftime('%d %b %Y')}{highlight} — {label}")

    if not parsed:
        st.caption("No calendar events loaded.")
