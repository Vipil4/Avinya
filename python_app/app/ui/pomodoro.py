from __future__ import annotations

import datetime as dt
import time

import streamlit as st

from app.storage import StudentStore
from app.ui.components import save_profile


def render(store: StudentStore) -> None:
    st.markdown("#### ⏱ Pomodoro")
    profile = st.session_state["profile"]
    pom = profile.setdefault("pomodoro", {"sessions": [], "streak": 0, "last_date": ""})

    if "pom_running" not in st.session_state:
        st.session_state["pom_running"] = False
        st.session_state["pom_minutes"] = 25
        st.session_state["pom_start_ts"] = None

    minutes = st.select_slider("Session length (minutes)", options=[15, 25, 45, 60], value=st.session_state["pom_minutes"])
    st.session_state["pom_minutes"] = minutes

    col1, col2 = st.columns(2)
    if not st.session_state["pom_running"]:
        if col1.button("▶ Start", type="primary"):
            st.session_state["pom_running"] = True
            st.session_state["pom_start_ts"] = time.time()
            st.rerun()
    else:
        elapsed = time.time() - st.session_state["pom_start_ts"]
        remaining = max(0, minutes * 60 - elapsed)
        mins, secs = divmod(int(remaining), 60)
        col1.markdown(f"### {mins:02d}:{secs:02d}")
        if col2.button("⏸ Stop"):
            _log_session(pom, minutes, store)
            st.session_state["pom_running"] = False
            st.rerun()
        if remaining <= 0:
            _log_session(pom, minutes, store)
            st.session_state["pom_running"] = False
            st.success(f"Session complete! {minutes} minutes logged.")
            st.rerun()
        else:
            time.sleep(1)
            st.rerun()

    st.caption(f"Streak: {pom.get('streak', 0)} days  ·  {len(pom.get('sessions', []))} sessions logged")


def _log_session(pom: dict, minutes: int, store: StudentStore) -> None:
    today = dt.date.today().isoformat()
    if pom.get("last_date") != today:
        pom["streak"] = pom.get("streak", 0) + 1
        pom["last_date"] = today
    pom.setdefault("sessions", []).append({"mins": minutes, "date": today})
    save_profile(store, st.session_state["student_id"])
