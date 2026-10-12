import subprocess
import os
import logging
from typing import Tuple, Optional

log = logging.getLogger("fable.sandbox")

def run_tests(test_target: Optional[str] = None) -> Tuple[bool, str]:
    """Runs pytest targeted to a specific file inside an ephemeral Docker container."""
    workspace_dir = os.path.abspath(os.getcwd())
    
    cmd = [
        "docker", "run",
        "--rm",                               # Destroy container immediately after exit
        "--memory", "256m",                   # OOM Protection: Cap memory at 256MB
        "--cpus", "0.5",                      # CPU limit: Prevent host resource exhaustion
        "-v", f"{workspace_dir}:/workspace",  # Mount the project directory
        "-w", "/workspace",                   # Set working directory
        "python:3.11-slim",                   # Minimal footprint Python base image
        "sh", "-c"                            # Execute inner commands
    ]
    
    # Inner container command: Install pytest, then run the tests
    inner_cmd = "pip install pytest --quiet && pytest -v"
    if test_target:
        inner_cmd += f" {test_target}"
    else:
        inner_cmd += " tests/"
        
    cmd.append(inner_cmd)
    
    log.info("🐳 [Sandbox] Spinning up ephemeral Docker container...")
    
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=45 
        )
        return (proc.returncode == 0), proc.stdout
    except subprocess.TimeoutExpired:
        log.error("⏳ [Sandbox] Container execution timed out. Forcibly killed.")
        return False, "Error: Execution timed out after 45 seconds. Check for infinite loops."
    except Exception as e:
        log.error(f"❌ [Sandbox] Docker execution failed: {e}")
        return False, str(e)
