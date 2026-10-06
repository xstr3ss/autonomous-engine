import docker
import tempfile
import os
import sys

class CodeSandbox:
    def __init__(self):
        print("🐳 [Sandbox] Connecting to Docker daemon...")
        try:
            self.client = docker.from_env()
            self.client.ping()
        except Exception:
            print("❌ [Sandbox] ERROR: Could not connect to Docker.")
            print("   Please ensure Docker Desktop is running and WSL integration is enabled.")
            sys.exit(1)
            
        print("🐳 [Sandbox] Pulling lightweight Python Alpine image (if not cached)...")
        self.client.images.pull("python:3.10-alpine")

    def test_patch(self, patched_code: str) -> tuple[bool, str]:
        """Runs the patched code in an isolated Docker container with strict resource limits."""
        # Create a temporary directory that automatically deletes itself
        with tempfile.TemporaryDirectory() as temp_dir:
            script_path = os.path.join(temp_dir, "script.py")
            
            # Write the AI's patch to the file
            with open(script_path, "w") as f:
                f.write(patched_code)
                
            # Append a strict CI/CD test suite to verify the logic actually works
            test_assertions = """
# --- Automated CI/CD Test Suite ---
try:
    assert authenticate('shyam') == True, "Failed valid user auth"
    assert authenticate('') == False, "Failed empty user auth"
    assert authenticate(None) == False, "Failed None user auth"
    print("✅ All sandbox tests passed successfully.")
except Exception as e:
    print(f"❌ Test Failed: {e}")
    exit(1)
"""
            with open(script_path, "a") as f:
                f.write(test_assertions)

            try:
                print("🛡️  [Sandbox] Executing code in isolated container (128MB RAM limit)...")
                # Run the container with strict security boundaries
                logs = self.client.containers.run(
                    "python:3.10-alpine",
                    command=["python", "/app/script.py"],
                    volumes={temp_dir: {'bind': '/app', 'mode': 'ro'}},
                    working_dir="/app",
                    remove=True,        # Instantly delete container after run
                    stderr=True,
                    stdout=True,
                    mem_limit="128m",   # Enterprise security: prevent memory leaks
                    network_disabled=True # Enterprise security: block internet access
                )
                return True, logs.decode('utf-8').strip()
                
            except docker.errors.ContainerError as e:
                # The script failed (exit code != 0)
                return False, e.stderr.decode('utf-8').strip()

if __name__ == "__main__":
    # Quick local test
    sandbox = CodeSandbox()
    good_code = "def authenticate(user):\n    return bool(user)"
    success, output = sandbox.test_patch(good_code)
    print(f"Test Result: {success} | Output: {output}")
