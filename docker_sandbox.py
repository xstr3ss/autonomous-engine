import subprocess
import os
import atexit
from typing import Tuple

class CodeSandbox:
    """
    Phase 3 Persistent Zero-Trust Execution Sandbox.
    Maintains a living container to allow the AI to run bash commands
    and explore the codebase dynamically, mimicking a real developer environment.
    """
    def __init__(self):
        self.container_name = "core_controller_sandbox"
        self.cwd = os.getcwd()
        self._boot_daemon()
        # Ensure cleanup when the engine shuts down or crashes
        atexit.register(self.shutdown)

    def _boot_daemon(self) -> None:
        """Boots the persistent container and installs dependencies once."""
        print("🐳 [Sandbox] Booting persistent microVM...")
        # Clean up any lingering ghosts from previous runs
        subprocess.run(["docker", "rm", "-f", self.container_name], capture_output=True)
        
        # Start the background daemon
        cmd = [
            "docker", "run", "-d", 
            "--name", self.container_name,
            "-v", f"{self.cwd}:/app",
            "-w", "/app",
            "python:3.9-slim",
            "sleep", "infinity"
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        
        print("📦 [Sandbox] Provisioning testing environment (pytest)...")
        # Install pytest once, saving massive time on subsequent loops
        self.run_bash("pip install pytest --quiet")
        print("✅ [Sandbox] Persistent environment active and ready.")

    def run_bash(self, command: str) -> Tuple[bool, str]:
        """
        Executes an arbitrary bash command securely inside the container.
        
        Args:
            command (str): The shell command to run (e.g., 'grep -r "API" .')
            
        Returns:
            Tuple[bool, str]: (Success status, stdout or stderr output)
        """
        # We wrap the command in sh -c to support pipes and shell built-ins
        cmd = ["docker", "exec", self.container_name, "sh", "-c", command]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        output = result.stdout if result.returncode == 0 else result.stderr
        return result.returncode == 0, output.strip()

    def test_patch(self, files_dict: dict = None) -> Tuple[bool, str]:
        """
        Executes the test suite. 
        Because the workspace is volume-mounted, local file changes made by 
        the DiffEngine are instantly reflected inside the container.
        """
        return self.run_bash("pytest")

    def shutdown(self) -> None:
        """Kills and removes the persistent container to free resources."""
        subprocess.run(["docker", "rm", "-f", self.container_name], capture_output=True)
