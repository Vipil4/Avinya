"""Loads the static knowledge-base JSON assets. All reads go through
`_safe_load_json`, which never raises on a missing/corrupted file — a
lesson learned the hard way from the original app, where dozens of
unguarded JSON.parse(localStorage...) calls could crash the page on a
single bad value. Reference data here is read-only and shipped with the
app, so corruption is unlikely, but the guard costs nothing."""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path

from config import settings
from app.data.models import Course, Faculty, Formula

logger = logging.getLogger(__name__)


def _safe_load_json(path: Path, default):
    try:
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning("Could not load %s (%s); using default.", path, e)
        return default


@lru_cache(maxsize=1)
def get_courses() -> list[Course]:
    raw = _safe_load_json(settings.assets_dir / "courses.json", [])
    return [Course.from_dict(d) for d in raw]


def get_course_by_code(code: str) -> Course | None:
    for c in get_courses():
        if c.code == code:
            return c
    return None


def search_courses(query: str = "") -> list[Course]:
    q = (query or "").strip().lower()
    if not q:
        return get_courses()
    out = []
    for c in get_courses():
        haystack = " ".join(
            [c.name, c.code, c.term, c.professor, " ".join(c.topics), " ".join(c.frameworks)]
        ).lower()
        if q in haystack:
            out.append(c)
    return out


@lru_cache(maxsize=1)
def get_faculty() -> list[Faculty]:
    raw = _safe_load_json(settings.assets_dir / "faculty.json", [])
    return [Faculty.from_dict(d) for d in raw]


def search_faculty(query: str = "", area: str = "all") -> list[Faculty]:
    q = (query or "").strip().lower()
    out = []
    for f in get_faculty():
        if area == "practice" and f.tag != "practice":
            continue
        if area == "retired" and f.tag != "retired":
            continue
        if area not in ("all", "practice", "retired") and (f.area != area or f.tag):
            continue
        haystack = " ".join([f.name, f.research, f.role, f.email]).lower()
        if not q or q in haystack:
            out.append(f)
    return out


@lru_cache(maxsize=1)
def get_formulas() -> list[Formula]:
    raw = _safe_load_json(settings.assets_dir / "formulas.json", [])
    return [Formula.from_dict(d) for d in raw]


def search_formulas(query: str = "", category: str = "all") -> list[Formula]:
    q = (query or "").strip().lower()
    out = []
    for form in get_formulas():
        if category != "all" and form.category != category:
            continue
        haystack = " ".join([form.name, form.description, form.course]).lower()
        if not q or q in haystack:
            out.append(form)
    return out


@lru_cache(maxsize=1)
def get_academic_calendar() -> dict[str, tuple[str, str]]:
    """Keys are 'YYYY-M-D' (M is 0-indexed, matching the original JS
    Date.getMonth() convention), values are (kind, label) where kind is
    'cl' (class) or 'ex' (exam)."""
    raw = _safe_load_json(settings.assets_dir / "academic_calendar.json", {})
    return {k: tuple(v) for k, v in raw.items()}


@lru_cache(maxsize=1)
def get_mcp_servers() -> dict[str, str]:
    return _safe_load_json(settings.assets_dir / "mcp_servers.json", {})
