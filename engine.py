import os
import logging
import subprocess
from config import Config
from llm import LLMClient
from parser import parse_file_blocks, extract_code
from sandbox import run_tests

logging.basicConfig(level=logging.INFO, format="%(message)s", force=True)
log = logging.getLogger("fable.engine")

class SelfHealingEngine:
    def __init__(self):
        log.info("🚨 [Engine] Initializing Universal Agentic Engine...")
        self.cfg = Config()
        self.llm = LLMClient(self.cfg)
        self.commit_on_fail = (os.getenv("FABLE_TDD_COMMIT_ON_FAIL", "0") == "1")

    def _write_files(self, response_text: str):
        blocks = parse_file_blocks(response_text)
        written = {}
        for file_path, body in blocks:
            code = extract_code(body)
            dir_name = os.path.dirname(file_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)
            written[file_path] = code
            log.info(f"✅ [Engine] Updated {file_path}")
        return written

    def resolve_error(self, error_output: str, files_context: dict = None):
        log.info("🔧 [Engine] Resolving error via self-healing loop...")
        success, current_error = False, error_output
        retries = 0
        
        if files_context is None:
            files_context = {}

        while not success and retries < 3:
            retries += 1
            log.info(f"❌ [TDD] Self-healing round {retries}/3")
            
            # Inject the current code context so the AI isn't flying blind
            code_context = ""
            if files_context:
                code_context = "Current Files:\n" + "\n".join([f"FILE: {k}\n{v}" for k, v in files_context.items()])
            
            repair_prompt = f"{code_context}\n\nThe test suite failed with these errors:\n{current_error}\n\nFix the code. If the tests have a ModuleNotFoundError, update the test file to include 'import sys, os; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), \"..\")))' before the imports. Output ONLY the repaired files using the 'FILE: filename.py' format."
            
            repair_response = self.llm.generate(repair_prompt, force_cloud=True, slow=True)
            new_files = self._write_files(repair_response)
            
            # Update context with the newly repaired files for the next round
            files_context.update(new_files)
            
            log.info("🧪 [TDD] Re-running pytest...")
            success, current_error = run_tests()
        
        self._handle_git_commit(success=success)
        return success

    def run(self, prompt: str):
        log.info("🔄 [Agent Loop] Attempt 1/2...")
        code_prompt = f"Write Python code for this feature. Output your code using the exact format 'FILE: filename.py\\n```python\\n<code>\\n```'. Feature:\n{prompt}"
        code_response = self.llm.generate(code_prompt)
        
        files = self._write_files(code_response)
        if not files:
            log.warning("⚠️ Local SLM failed to format. Escalating to Cloud...")
            code_response = self.llm.generate(code_prompt, force_cloud=True, slow=True)
            files = self._write_files(code_response)
            if not files:
                log.error("🛑 [Engine] Fatal: Cloud model also failed formatting.")
                return

        log.info("🧪 [TDD] Writing test suite...")
        file_context = "\n".join([f"FILE: {k}\n{v}" for k, v in files.items()])
        test_prompt = f"Write a pytest suite for these files. Output using the exact format 'FILE: tests/test_filename.py\\n```python\\n<code>\\n```'.\n\nFiles:\n{file_context}"
        
        test_response = self.llm.generate(test_prompt, slow=True)
        test_files = self._write_files(test_response)
        
        if not test_files:
            log.warning("⚠️ Local SLM failed test generation. Escalating to Cloud...")
            test_response = self.llm.generate(test_prompt, force_cloud=True, slow=True)
            test_files = self._write_files(test_response)
            if not test_files:
                log.error("🛑 [TDD] Could not produce a valid test suite.")
                self._handle_git_commit(success=False)
                return

        # Combine source and test files so the repair loop has full visibility
        all_files = {**files, **test_files}

        log.info("🧪 [TDD] Running pytest in sandbox...")
        success, error_output = run_tests()
        
        if not success:
            return self.resolve_error(error_output, all_files)

        if success:
            log.info("✅ [TDD] Green: All tests passed!")
            self._handle_git_commit(success=True)
        else:
            self._handle_git_commit(success=False)

    def _handle_git_commit(self, success: bool):
        if success or self.commit_on_fail:
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", "Auto-commit: Fable TDD loop"], check=True)
            log.info("📝 [Git] Committed successfully.")
        else:
            log.error("📝 [Git] Not committing: the tests did not pass.")
