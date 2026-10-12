import os
import logging
import subprocess

log = logging.getLogger("fable.git")

class GitManager:
    def __init__(self):
        self.commit_on_fail = (os.getenv("FABLE_TDD_COMMIT_ON_FAIL", "0") == "1")

    def commit(self, success: bool, message: str = "Auto-commit: Fable Multi-Agent Loop"):
        if success or self.commit_on_fail:
            try:
                subprocess.run(["git", "add", "."], check=True)
                subprocess.run(["git", "commit", "-m", message], check=True)
                log.info("📝 [Git] Committed successfully.")
            except subprocess.CalledProcessError as e:
                log.error(f"📝 [Git] Commit failed: {e}")
        else:
            log.error("📝 [Git] Not committing: tests did not pass.")
