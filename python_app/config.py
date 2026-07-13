"""Central settings for Avinya. Everything reads from here — no module
should call os.environ directly."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str
    model: str
    max_tokens: int
    data_dir: Path
    assets_dir: Path

    @property
    def has_api_key(self) -> bool:
        return bool(self.anthropic_api_key)


def load_settings() -> Settings:
    data_dir = Path(os.environ.get("AVINYA_DATA_DIR", BASE_DIR / "student_data"))
    data_dir.mkdir(parents=True, exist_ok=True)
    return Settings(
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        model=os.environ.get("AVINYA_MODEL", "claude-sonnet-5"),
        max_tokens=int(os.environ.get("AVINYA_MAX_TOKENS", "3000")),
        data_dir=data_dir,
        assets_dir=BASE_DIR / "app" / "data" / "assets",
    )


settings = load_settings()
