import os
import logging
import subprocess
from config import Config
from llm import LLMClient
from parser import parse_file_blocks, extract_code
from docker_sandbox import run_tests
from memory import VectorMemory

logging.basicConfig(level=logging.INFO, format="%(message)s", force=True)
log = logging.getLogger("fable.engine")

class SelfHealingEngine:
    def __init__(self):
        log.info("🚨 [Engine] Initializing Universal Agentic Engine...")
        self.cfg = Config()
        self.llm = LLMClient(self.cfg)
        self.memory = VectorMemory()
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

    def _generate_contract(self, objective: str) -> str:
        contract_prompt = (
            f"Define ONLY the Python function signature(s) and type annotations required for this objective:\n"
            f"\"{objective}\"\n\n"
            f"Provide no implementation body—use '...' or 'pass'. Return pure Python signatures."
        )
        return self.llm.generate(contract_prompt, slow=False)

    def resolve_error(self, error_output: str, files_context: dict, target_test: str):
        log.info("🔧 [Engine] Resolving error via self-healing loop...")
        success, current_error = False, error_output
        retries = 0
        
        similar_repairs = self.memory.recall_similar_errors(current_error)
        memory_context = ""
        if similar_repairs:
            log.info(f"🧠 [Memory] Retrieved {len(similar_repairs)} similar historical fixes.")
            memory_context = "PAST SUCCESSFUL REPAIRS FOR SIMILAR ERRORS:\n" + "\n".join(
                [f"File: {r.get('file_path')}\nFix: {r.get('code_snapshot')}" for r in similar_repairs]
            )

        while not success and retries < 3:
            retries += 1
            log.info(f"❌ [TDD] Self-healing round {retries}/3")

            code_context = "Current Files:\n" + "\n".join([f"FILE: {k}\n{v}" for k, v in files_context.items()])

            repair_prompt = (
                f"{code_context}\n\n"
                f"{memory_context}\n\n"
                f"Test failure output:\n{current_error}\n\n"
                f"Fix the code and test synchronization. Output ONLY repaired files using 'FILE: filename.py'."
            )

            repair_response = self.llm.generate(repair_prompt, force_cloud=True, slow=True)
            new_files = self._write_files(repair_response)
            files_context.update(new_files)

            log.info(f"🧪 [TDD] Re-running {target_test}...")
            success, current_error = run_tests(test_target=target_test)

        if success:
            for filename, code in files_context.items():
                self.memory.store_repair_context(current_error, code, filename)

        self._handle_git_commit(success=success)
        return success

    def run(self, prompt: str):
        log.info("📐 [Engine] Generating interface contract...")
        contract = self._generate_contract(prompt)

        log.info("🔄 [Agent Loop] Generating implementation from contract...")
        code_prompt = (
            f"Implement the following feature conforming STRICTLY to this interface contract:\n"
            f"{contract}\n\n"
            f"CRITICAL RULES:\n"
            f"1. You MUST output using EXACTLY this format:\n"
            f"FILE: filename.py\n```python\n<code>\n```\n"
            f"2. DO NOT output any conversational text before or after. Start immediately with FILE:. Feature:\n{prompt}"
        )
        code_response = self.llm.generate(code_prompt)
        files = self._write_files(code_response)

        if not files:
            log.warning("⚠️ Escalating code generation to Cloud...")
            code_response = self.llm.generate(code_prompt, force_cloud=True, slow=True)
            files = self._write_files(code_response)
            if not files:
                log.error("🛑 [Engine] Fatal: Failed to generate source files.")
                log.error(f"🔍 [DEBUG] RAW LLM OUTPUT THAT BROKE THE PARSER:\n{code_response}")
                return

        log.info("🧪 [TDD] Writing contract-aligned test suite...")
        file_context = "\n".join([f"FILE: {k}\n{v}" for k, v in files.items()])
        test_prompt = (
            f"Write a pytest suite for these files conforming to this contract:\n{contract}\n\n"
            f"Files:\n{file_context}\n\n"
            f"CRITICAL RULES:\n"
            f"1. Output format: 'FILE: tests/test_filename.py\\n```python\\n<code>\\n```'.\n"
            f"2. No conversational text."
        )
        test_response = self.llm.generate(test_prompt, slow=True)
        test_files = self._write_files(test_response)

        if not test_files:
            log.warning("⚠️ Escalating test generation to Cloud...")
            test_response = self.llm.generate(test_prompt, force_cloud=True, slow=True)
            test_files = self._write_files(test_response)
            if not test_files:
                log.error("🛑 [TDD] Fatal: Failed to generate test files.")
                log.error(f"🔍 [DEBUG] RAW LLM OUTPUT THAT BROKE THE PARSER:\n{test_response}")
                return

        target_test_file = next((f for f in test_files.keys() if f.startswith("tests/")), None)
        all_files = {**files, **test_files}

        log.info(f"🧪 [TDD] Running sandbox on target: {target_test_file}...")
        success, error_output = run_tests(test_target=target_test_file)

        if not success:
            return self.resolve_error(error_output, all_files, target_test_file)

        log.info("✅ [TDD] Green: All targeted tests passed!")
        
        for filename, code in all_files.items():
            self.memory.store_repair_context("Initial TDD Run", code, filename)
            
        self._handle_git_commit(success=True)

    def _handle_git_commit(self, success: bool):
        if success or self.commit_on_fail:
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", "Auto-commit: Fable TDD loop"], check=True)
            log.info("📝 [Git] Committed successfully.")
        else:
            log.error("📝 [Git] Not committing: tests did not pass.")
