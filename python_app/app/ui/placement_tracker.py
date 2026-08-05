"""Placement Tracker.

In the original app, addPlacement()/savePlacement()/renderPlacements()
were fully implemented in JS but referenced DOM ids (#place-form,
#place-co, #placement-list, ...) that did not exist anywhere in the
shipped HTML — the feature was advertised in the README and in in-app
hint text, but had no actual entry point in the UI. This page is the
fixed version: an actual form, wired to actual storage.
"""
from __future__ import annotations

import time

import streamlit as st

from app.storage import StudentStore
from app.ui.components import save_profile

_STATUSES = ["research", "applied", "interview", "offer", "rejected"]
_STATUS_LABEL = {
    "research": "🔎 Researching",
    "applied": "📨 Applied",
    "interview": "🗣 Interview",
    "offer": "🎉 Offer",
    "rejected": "❌ Rejected",
}


def render(store: StudentStore) -> None:
    st.markdown("### 📌 Placement Tracker")
    profile = st.session_state["profile"]
    placements = profile.setdefault("placements", [])

    active = [p for p in placements if p["status"] not in ("offer", "rejected")]
    offers = [p for p in placements if p["status"] == "offer"]
    col1, col2, col3 = st.columns(3)
    col1.metric("Total", len(placements))
    col2.metric("Active", len(active))
    col3.metric("Offers", len(offers))

    with st.form("add_placement_form", clear_on_submit=True):
        st.markdown("**Add a company**")
        c1, c2 = st.columns(2)
        company = c1.text_input("Company")
        role = c2.text_input("Role")
        date = st.text_input("Target date (optional)")
        submitted = st.form_submit_button("Add")
        if submitted:
            if not company or not role:
                st.warning("Enter company and role.")
            else:
                placements.insert(0, {
                    "id": int(time.time() * 1000),
                    "co": company, "role": role, "status": "research", "date": date, "notes": "",
                })
                save_profile(store, st.session_state["student_id"])
                st.rerun()

    st.divider()
    if not placements:
        st.caption("Track your target companies, application status, and interviews here.")
        return

    for p in list(placements):
        c1, c2, c3 = st.columns([3, 2, 1])
        c1.write(f"**{p['co']}**  \n{p['role']}" + (f" · {p['date']}" if p.get("date") else ""))
        new_status = c2.selectbox(
            "Status", _STATUSES, index=_STATUSES.index(p["status"]),
            format_func=lambda s: _STATUS_LABEL[s], key=f"status_{p['id']}", label_visibility="collapsed",
        )
        if new_status != p["status"]:
            p["status"] = new_status
            save_profile(store, st.session_state["student_id"])
            st.rerun()
        if c3.button("✕", key=f"del_{p['id']}"):
            profile["placements"] = [x for x in placements if x["id"] != p["id"]]
            save_profile(store, st.session_state["student_id"])
            st.rerun()
