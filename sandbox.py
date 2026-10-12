import subprocess
import os
from typing import Tuple, Optional

def run_tests(test_target: Optional[str] = None) -> Tuple[bool, str]:
    """Runs pytest targeted to a specific file or the whole suite."""
    cmd = ["pytest", "-v"]
    if test_target and os.path.exists(test_target):
        cmd.append(test_target)
    else:
        cmd.append("tests/")

    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.abspath(os.getcwd())

    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env
    )
    passed = (proc.returncode == 0)
    return passed, proc.stdout
