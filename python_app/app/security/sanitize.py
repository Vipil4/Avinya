"""Single source of truth for output-escaping and upload validation.

The original app had two separate file-upload code paths — one validated
MIME type and size, the other (an older, still-reachable input) validated
neither. Here there is exactly one `validate_upload` function and every UI
entry point calls it, so that class of inconsistency can't recur.

Similarly, the original had several places where an LLM response was
injected into the page via innerHTML with no escaping, producing a stored
XSS vulnerability triggerable via prompt injection. Streamlit's st.markdown
/st.write do not render HTML unless unsafe_allow_html=True is passed, so as
a rule we never pass unsafe_allow_html=True with LLM- or user-derived text.
escape_html() exists for the rare cases (custom badges/styling) where we do
need unsafe_allow_html, so that path stays safe too if it's ever used with
dynamic text.
"""
from __future__ import annotations

import html
from dataclasses import dataclass

ALLOWED_UPLOAD_MIME_TYPES = {
    "application/pdf": "pdf",
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/webp": "webp",
}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


def escape_html(text: str) -> str:
    """Escapes &, <, > (and quotes) — safe to interpolate into HTML."""
    return html.escape(text or "", quote=True)


@dataclass(frozen=True)
class UploadValidationResult:
    ok: bool
    reason: str = ""


def validate_upload(filename: str, mime_type: str, size_bytes: int) -> UploadValidationResult:
    if mime_type not in ALLOWED_UPLOAD_MIME_TYPES:
        return UploadValidationResult(
            ok=False,
            reason=f"Unsupported file type '{mime_type}'. Please upload a PDF or image (PNG, JPG, WebP).",
        )
    if size_bytes <= 0:
        return UploadValidationResult(ok=False, reason="File is empty.")
    if size_bytes > MAX_UPLOAD_BYTES:
        mb = size_bytes / (1024 * 1024)
        return UploadValidationResult(
            ok=False, reason=f"File too large ({mb:.1f} MB). Please use files under 10 MB."
        )
    return UploadValidationResult(ok=True)
