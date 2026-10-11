from __future__ import annotations
import hashlib
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

_SIG_RE = re.compile(r"^(?:FAILED|ERROR) .*$", re.MULTILINE)
_SUMMARY_RE = re.compile(r"\d+ (?:passed|failed|errors?|skipped|deselected|xfailed|xpassed)")
_SECRET_HINTS = ("KEY", "TOKEN", "SECRET", "PASSWORD", "PASSWD", "CREDENTIAL")

def clip_text(text: str, limit: int) -> str:
    """Shorten long text, keeping the start and (more of) the end, where pytest puts its summary."""
    if len(text) <= limit:
        return text
    head = limit * 3 // 10
    return text[:head] + "\n...[truncated]...\n" + text[-(limit - head):]

def failure_signature(output: str) -> str:
    """Stable fingerprint of a failure, to notice when a fix attempt changed nothing."""
    lines = _SIG_RE.findall(output) or [output[-500:]]
    return hashlib.sha1("\n".join(sorted(lines)).encode("utf-8", "replace")).hexdigest()

def sandbox_env(workspace: Path) -> dict:
    """Environment for generated code: no API keys, tokens or passwords."""
    env = {k: v for k, v in os.environ.items() if not any(h in k.upper() for h in _SECRET_HINTS)}
    env["PYTHONPATH"] = os.pathsep.join([str(workspace)] + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else []))
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["FABLE_SANDBOX"] = "1"
    return env

def limit_resources(cpu_seconds: int) -> Callable[[], None]:
    def apply() -> None:
        import resource  # POSIX only
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))
        resource.setrlimit(resource.RLIMIT_FSIZE, (200 * 2**20, 200 * 2**20))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    return apply

@dataclass
class PytestResult:
    returncode: int
    output: str
    timed_out: bool = False

    @property
    def passed(self) -> bool:
        return self.returncode == 0 and not self.timed_out

    @property
    def no_tests(self) -> bool:
        return self.returncode == 5

    @property
    def summary(self) -> str:
        if self.timed_out:
            return "timed out"
        for line in reversed(self.output.strip().splitlines()):
            if _SUMMARY_RE.search(line):
                return line.strip(" =")
        return f"exit code {self.returncode}"

@dataclass
class TddReport:
    status: str                    # "passed" | "failed" | "skipped" | "unavailable"
    summary: str = ""
    repairs: int = 0
    files: list = field(default_factory=list)   # test files and any source files the loop touched

    @property
    def ok(self) -> bool:
        return self.status in ("passed", "skipped")
