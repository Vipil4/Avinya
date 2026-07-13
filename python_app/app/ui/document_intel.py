"""Document Intelligence — upload a PDF/image, Claude analyses it.

The original app had two upload code paths: one (docSelectFile) validated
file type and a 10MB size cap, the other (an older, still-reachable input
bound to processFile) validated neither and would ship a 25MB+ or
wrong-type file straight to the API. Here there is exactly one upload
entry point and it always goes through `validate_upload`.
"""
from __future__ import annotations

import base64

import streamlit as st

from app.llm.prompts import SYS_DOCUMENT_ANALYSIS
from app.security import validate_upload
from app.storage import StudentStore
from app.ui.components import require_api_key, save_profile

_MODES = {
    "notes": "Generate structured study notes from this document.",
    "questions": "Generate 5 practice questions (with answers) based only on this document.",
    "summary": "Summarize this document in a clean, structured format.",
    "formulas": "Extract every formula/framework mentioned in this document, with a one-line explanation each.",
}


def render(store: StudentStore) -> None:
    st.markdown("### 📄 Document Intelligence")
    st.caption("Upload a PDF or image — Claude will analyse it and link it to the DoMS curriculum.")

    uploaded = st.file_uploader("Choose a file", type=["pdf", "png", "jpg", "jpeg", "webp"])
    mode = st.radio("Mode", list(_MODES.keys()), format_func=lambda k: k.capitalize(), horizontal=True)

    if uploaded is None:
        return

    file_bytes = uploaded.getvalue()
    validation = validate_upload(uploaded.name, uploaded.type, len(file_bytes))
    if not validation.ok:
        st.error(validation.reason)
        return

    st.caption(f"📄 {uploaded.name} ({len(file_bytes) / 1024:.0f} KB)")

    if st.button("Analyse document", type="primary"):
        if not require_api_key():
            return

        b64 = base64.b64encode(file_bytes).decode()
        is_pdf = uploaded.type == "application/pdf"
        content_block = (
            {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": b64}}
            if is_pdf
            else {"type": "image", "source": {"type": "base64", "media_type": uploaded.type, "data": b64}}
        )
        messages = [
            {
                "role": "user",
                "content": [content_block, {"type": "text", "text": _MODES[mode]}],
            }
        ]
        extra_headers = {"anthropic-beta": "pdfs-2024-09-25"} if is_pdf else None

        with st.spinner("Analysing document... this may take 15-30s."):
            result = st.session_state["client"].complete(
                messages=messages, system=SYS_DOCUMENT_ANALYSIS, max_tokens=2500, extra_headers=extra_headers
            )

        if result.ok:
            st.markdown(result.text)
            if st.button("💾 Save to Notes"):
                profile = st.session_state["profile"]
                notes = profile.setdefault("notes", {})
                key = "general"
                notes[key] = (notes.get(key, "") + f"\n\n--- From {uploaded.name} ---\n{result.text}").strip()
                save_profile(store, st.session_state["student_id"])
                st.success("Saved to General Notes.")
        else:
            st.error(result.error)
