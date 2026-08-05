"""Per-student JSON-file storage — the equivalent of the original app's
localStorage, but hardened against two bugs found during testing of the
original:

1. Corrupted JSON on disk (crashed write, manual edit, disk issue) used to
   throw an uncaught exception from dozens of unguarded JSON.parse calls.
   `load()` here never raises for that reason — it logs a warning and
   returns a fresh default profile instead.

2. Two browser tabs/sessions editing the same student's notes concurrently
   used to silently overwrite each other with no warning. `save()` here
   is optimistic-concurrency-checked: every profile carries a `_version`
   counter, and a save whose `expected_version` doesn't match what's on
   disk raises `ConflictError` instead of clobbering, so the caller (the
   UI layer) can tell the student their data changed elsewhere.
"""
from __future__ import annotations

import fcntl
import json
import logging
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from config import settings

logger = logging.getLogger(__name__)

_SAFE_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")


class ConflictError(Exception):
    """Raised when saving a profile whose expected_version is stale —
    someone else (another tab/session) saved a newer version first."""


def default_profile() -> dict:
    return {
        "_version": 0,
        "name": "",
        "roll": "",
        "email": "",
        "term": "",
        "specialization": "",
        "goal": "",
        "work": "",
        "notes": {},  # course_code -> text
        "mcq_history": [],
        "pomodoro": {"sessions": [], "streak": 0, "last_date": ""},
        "placements": [],
        "memory_log": [],
        "vault": [],
    }


@dataclass
class StudentStore:
    data_dir: Path = field(default_factory=lambda: settings.data_dir)

    def _path_for(self, student_id: str) -> Path:
        if not _SAFE_ID_RE.match(student_id):
            raise ValueError(f"Invalid student_id: {student_id!r}")
        return self.data_dir / f"{student_id}.json"

    def load(self, student_id: str) -> dict:
        path = self._path_for(student_id)
        if not path.exists():
            return default_profile()
        try:
            with path.open(encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("profile root is not an object")
            merged = default_profile()
            merged.update(data)
            return merged
        except (json.JSONDecodeError, ValueError, OSError) as e:
            logger.warning("Corrupted profile for %s (%s); starting fresh.", student_id, e)
            return default_profile()

    def save(self, student_id: str, data: dict, expected_version: int | None) -> dict:
        """Writes `data` if `expected_version` still matches what's on
        disk (or the file doesn't exist yet). Returns the saved dict
        (with an incremented _version). Raises ConflictError otherwise."""
        path = self._path_for(student_id)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Use an advisory lock on a sidecar file so read-check-write is
        # atomic across concurrent processes/threads.
        lock_path = path.with_suffix(".lock")
        with lock_path.open("w") as lock_f:
            fcntl.flock(lock_f, fcntl.LOCK_EX)
            try:
                current_version = 0
                if path.exists():
                    try:
                        with path.open(encoding="utf-8") as f:
                            on_disk = json.load(f)
                        current_version = int(on_disk.get("_version", 0))
                    except (json.JSONDecodeError, ValueError):
                        current_version = 0  # corrupted on-disk copy — safe to overwrite

                if expected_version is not None and current_version != expected_version:
                    raise ConflictError(
                        f"Profile for {student_id} was modified elsewhere "
                        f"(expected version {expected_version}, found {current_version})."
                    )

                to_write = dict(data)
                to_write["_version"] = current_version + 1
                to_write["_saved_at"] = time.time()

                tmp_path = path.with_suffix(".tmp")
                with tmp_path.open("w", encoding="utf-8") as f:
                    json.dump(to_write, f, indent=2, ensure_ascii=False)
                tmp_path.replace(path)
                return to_write
            finally:
                fcntl.flock(lock_f, fcntl.LOCK_UN)
