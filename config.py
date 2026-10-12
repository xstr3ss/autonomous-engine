from __future__ import annotations
import os
from dataclasses import dataclass, field
from pathlib import Path

def _env_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    return default if val is None else val.strip().lower() in {"1", "true", "yes", "on"}

def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default

@dataclass(frozen=True)
class Config:
    groq_api_key: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    local_url: str = field(default_factory=lambda: os.getenv("FABLE_LOCAL_URL", "http://localhost:11434/api/generate"))
    local_model: str = field(default_factory=lambda: os.getenv("FABLE_LOCAL_MODEL", "qwen2.5-coder:3b"))
    cloud_url: str = field(default_factory=lambda: os.getenv("FABLE_CLOUD_URL", "https://api.groq.com/openai/v1/chat/completions"))

    # Locked to a guaranteed active model
    cloud_model: str = field(default_factory=lambda: os.getenv("FABLE_CLOUD_MODEL", "llama-3.3-70b-versatile"))

    temperature: float = 0.2
    local_timeout: int = field(default_factory=lambda: _env_int("FABLE_LOCAL_TIMEOUT", 180))
    cloud_timeout: int = 120
    local_retries: int = 2
    local_cooldown: int = 60
    bash_timeout: int = 120
    workspace: Path = field(default_factory=Path.cwd)
    prefer_cloud: bool = field(default_factory=lambda: _env_bool("FABLE_PREFER_CLOUD", False))
    auto_commit: bool = field(default_factory=lambda: _env_bool("FABLE_AUTO_COMMIT", True))
    confirm_bash: bool = field(default_factory=lambda: _env_bool("FABLE_CONFIRM_BASH", False))

    # --- Test-driven loop ---
    tdd: bool = field(default_factory=lambda: _env_bool("FABLE_TDD", True))
    tdd_rounds: int = field(default_factory=lambda: _env_int("FABLE_TDD_ROUNDS", 3))
    tdd_timeout: int = field(default_factory=lambda: _env_int("FABLE_TDD_TIMEOUT", 60))
    tdd_commit_on_fail: bool = field(default_factory=lambda: _env_bool("FABLE_TDD_COMMIT_ON_FAIL", False))
    tdd_auto_install: bool = field(default_factory=lambda: _env_bool("FABLE_TDD_AUTO_INSTALL", True))
    tdd_context_chars: int = 6000
    tests_dir: str = "tests"
