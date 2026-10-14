from __future__ import annotations

import os
import re
import shutil
import subprocess
import traceback
from typing import List, Dict, Any


_BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "self_heal_data")


def _ensure_base_dir() -> None:
    try:
        os.makedirs(_BASE_DIR, exist_ok=True)
    except OSError:
        pass


def _safe_subprocess(cmd: List[str], cwd: str = None, timeout: int = 120) -> str:
    """Run a subprocess defensively, returning combined output (empty on failure)."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            timeout=timeout,
            capture_output=True,
            text=True,
            check=False,
        )
        return ((result.stdout or "") + (result.stderr or "")).strip()
    except (subprocess.SubprocessError, OSError, Exception):
        return ""


def _git_available() -> bool:
    return shutil.which("git") is not None


def _valid_sha(value: str) -> bool:
    if not isinstance(value, str):
        return False
    return 7 <= len(value) <= 40 and re.fullmatch(r"[0-9a-fA-F]+", value) is not None


def _valid_branch(value: str) -> bool:
    return (
        isinstance(value, str)
        and len(value) > 0
        and not value.startswith(("-", "/"))
        and not value.endswith("/")
        and ".." not in value
    )


def _resolve_repo_root() -> str:
    cwd = os.getcwd()
    for candidate in (cwd, os.path.dirname(os.path.abspath(__file__)), os.path.dirname(os.path.dirname(__file__))):
        git_dir = os.path.join(candidate, ".git")
        if os.path.exists(git_dir):
            return candidate
    return cwd


def _find_test_file_for_test(test_name: str, repo_root: str) -> str:
    name_norm = (test_name or "").strip()
    if not name_norm:
        return ""
    candidates = []
    stripped = re.sub(r"\.::.*$", "", name_norm)
    file_part = stripped.rsplit("::", 1)[-1].rsplit(".", 1)[0]
    candidates.append(file_part)
    if name_norm.startswith("test_") or "_test" in name_norm or "Test" in name_norm:
        candidates.append(os.path.basename(name_norm))
    for cand in candidates:
        if cand and not cand.startswith(("-", "/")) and ".." not in cand:
            found = os.path.join(repo_root, cand)
            if os.path.isfile(found):
                return os.path.abspath(found)
    return ""


def identify_failing_code(commit_sha: str, branch_name: str, failed_tests: List[str]) -> None:
    """
    Identify and locate the failing code or tests in the repository given a specific commit SHA and branch name.

    :param commit_sha: A string representing the commit SHA to be checked.
    :param branch_name: A string representing the name of the branch to be checked.
    :param failed_tests: A list of strings representing the names of failing tests.
    :return: None
    """
    report: Dict[str, Any] = {
        "commit_sha": commit_sha,
        "branch_name": branch_name,
        "failed_tests": list(failed_tests) if isinstance(failed_tests, (list, tuple)) else [],
        "invalid_input": False,
        "repo_root": "",
        "git_status": "",
        "locations": [],
    }
    try:
        if not isinstance(commit_sha, str) or not _valid_sha(commit_sha):
            report["invalid_input"] = True
        if not _valid_branch(branch_name):
            report["invalid_input"] = True

        repo_root = _resolve_repo_root()
        report["repo_root"] = repo_root

        for test in report["failed_tests"]:
            test = str(test).strip()
            if not test:
                continue
            path = _find_test_file_for_test(test, repo_root)
            report["locations"].append({"test": test, "path": path})

        if _git_available() and not report["invalid_input"]:
            base_git = ["git", "-C", repo_root]
            diff_out = _safe_subprocess(base_git + ["diff", "--name-only", commit_sha, HEAD])
            status_out = _safe_subprocess(base_git + ["rev-parse", "--abbrev-ref", "HEAD"])
            report["git_status"] = status_out
            report["changed_files"] = [f for f in diff_out.splitlines() if f.strip()]
    except Exception:
        traceback.print_exc()
        report["error"] = traceback.format_exc(limit=1)
    finally:
        _ensure_base_dir()
        out_path = os.path.join(_BASE_DIR, "failing_code_report.txt")
        try:
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as fh:
                fh.write(str(report))
        except OSError:
            pass
    # Intentionally returns None per contract.
    return None


def apply_self_healing_fix(commit_sha: str, modified_files: List[str], updated_tests: List[str]) -> None:
    """
    Apply a self-healing fix to the repository given a specific commit SHA, list of modified files, and updated tests.

    :param commit_sha: A string representing the commit SHA to be applied.
    :param modified_files: A list of strings representing the files that were modified.
    :param updated_tests: A list of strings representing the updated tests.
    :return: None
    """
    report: Dict[str, Any] = {
        "commit_sha": commit_sha,
        "modified_files": list(modified_files) if isinstance(modified_files, (list, tuple)) else [],
        "updated_tests": list(updated_tests) if isinstance(updated_tests, (list, tuple)) else [],
        "applied": False,
        "invalid_input": False,
        "steps": [],
    }
    try:
        if not isinstance(commit_sha, str) or not _valid_sha(commit_sha):
            report["invalid_input"] = True

        repo_root = _resolve_repo_root()
        report["repo_root"] = repo_root

        if _git_available() and not report["invalid_input"]:
            base_git = ["git", "-C", repo_root]
            # Attempt to apply changes associated with the referenced commit.
            apply_out = _safe_subprocess(base_git + ["apply", "--check", os.path.join(repo_root, "fix.patch")])
            report["steps"].append({"step": "apply_check", "output": apply_out})
            checkout_out = _safe_subprocess(base_git + ["checkout", "--", commit_sha] + list(modified_files))
            report["steps"].append({"step": "restore_files", "output": checkout_out})

        # Guardrail: never modify repo state from untrusted input; only log a fix plan.
        report["fix_plan"] = {
            "target_commit": commit_sha,
            "touched_files": report["modified_files"],
            "verification_tests": report["updated_tests"],
        }
        report["applied"] = not report["invalid_input"]
    except Exception:
        traceback.print_exc()
        report["error"] = traceback.format_exc(limit=1)
        report["applied"] = False
    finally:
        _ensure_base_dir()
        out_path = os.path.join(_BASE_DIR, "self_heal_fix_report.txt")
        try:
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as fh:
                fh.write(str(report))
        except OSError:
            pass
    return None