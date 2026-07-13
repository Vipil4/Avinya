"""Typed views over the static knowledge base (courses, faculty, formulas,
academic calendar). Kept as plain dataclasses — this data is read-only
reference content, not something we need an ORM for."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Course:
    term: str
    code: str
    name: str
    professor: str
    prof_role: str = ""
    topics: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    notes: str = ""
    co_profs: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> "Course":
        return cls(
            term=d.get("term", ""),
            code=d.get("code", ""),
            name=d.get("name", ""),
            professor=d.get("professor", ""),
            prof_role=d.get("profRole", ""),
            topics=d.get("topics", []) or [],
            frameworks=d.get("frameworks", []) or [],
            notes=d.get("notes", ""),
            co_profs=d.get("coProfs", []) or [],
        )


@dataclass(frozen=True)
class Faculty:
    name: str
    role: str
    area: str
    color: str
    initials: str
    email: str
    phone: str
    room: str
    research: str
    profile_url: str
    linkedin_url: str
    tag: str = ""  # '', 'practice', or 'retired'
    note: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "Faculty":
        return cls(
            name=d.get("name", ""),
            role=d.get("role", ""),
            area=d.get("area", ""),
            color=d.get("color", "#0a1628"),
            initials=d.get("init", ""),
            email=d.get("email", ""),
            phone=d.get("phone", ""),
            room=d.get("room", ""),
            research=d.get("research", ""),
            profile_url=d.get("url", ""),
            linkedin_url=d.get("li", d.get("url", "")),
            tag=d.get("tag", ""),
            note=d.get("note", ""),
        )


@dataclass(frozen=True)
class Formula:
    name: str
    category: str
    formula: str
    description: str = ""
    course: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "Formula":
        return cls(
            name=d.get("name", d.get("title", "")),
            category=d.get("cat", d.get("category", "")),
            formula=d.get("formula", d.get("expr", "")),
            description=d.get("desc", d.get("description", "")),
            course=d.get("course", ""),
        )
