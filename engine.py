from distiller import DistillationEngine
import logging
from config import Config
from llm import LLMClient
from parser import apply_patch
from docker_sandbox import run_tests
from memory import VectorMemory
from critic import CriticAgent
from git_ops import GitManager
from explorer import WorkspaceExplorer  # 🚨 NEW

logging.basicConfig(level=logging.INFO, format="%(message)s", force=True)
log = logging.getLogger("fable.engine")

class SelfHealingEngine:
    def __init__(self):
        log.info("🚨 [Engine] Initializing Autonomous Multi-Agent Engine...")
        self.cfg = Config()
        self.llm = LLMClient(self.cfg)
        self.memory = VectorMemory()
        self.critic = CriticAgent(self.llm)
        self.git = GitManager()
        self.explorer = WorkspaceExplorer(self.llm) 
        self.distiller = DistillationEngine() # 🚨 NEW
    def _write_files(self, response_text: str):
        try:
            return apply_patch(response_text)
        except Exception as e:
            log.error(f"⚠️ [Engine] Patch application failed: {e}")
            return {}

    def _generate_contract(self, objective: str, repo_context: str) -> str:
        prompt = (
            f"Based on this repository context:\n{repo_context}\n\n"
            f"Define ONLY the Python function signature(s) and type annotations required for this objective:\n"
            f"\"{objective}\"\n\n"
            f"Provide no implementation body—use '...' or 'pass'. Return pure Python signatures."
        )
        return self.llm.generate(prompt, slow=False)

    def _execute_with_critic(self, contract: str, files_context: dict, target_test: str) -> tuple[bool, str]:
        approved, feedback = self.critic.review(contract, files_context)
        if not approved:
            log.warning(f"✋ [Critic] Blocked execution: {feedback}")
            return False, f"CRITIC REJECTION:\n{feedback}"
            
        log.info(f"🧪 [TDD] Critic approved. Running sandbox on target: {target_test}...")
        return run_tests(test_target=target_test)

    def resolve_error(self, error_output: str, files_context: dict, target_test: str, contract: str):
        log.info("🔧 [Engine] Resolving error via self-healing loop...")
        success, current_error = False, error_output
        retries = 0
        
        similar_repairs = self.memory.recall_similar_errors(current_error)
        memory_context = ""
        if similar_repairs:
            log.info(f"🧠 [Memory] Retrieved {len(similar_repairs)} similar historical fixes.")
            memory_context = "PAST SUCCESSFUL REPAIRS:\n" + "\n".join(
                [f"File: {r.get('file_path')}\nFix: {r.get('code_snapshot')}" for r in similar_repairs]
            )

        while not success and retries < 3:
            retries += 1
            log.info(f"❌ [TDD] Self-healing round {retries}/3")
            code_context = "Current Files:\n" + "\n".join([f"FILE: {k}\n{v}" for k, v in files_context.items()])

            repair_prompt = (
                f"{code_context}\n\n{memory_context}\n\n"
                f"Failure output:\n{current_error}\n\n"
                f"Fix the code and test synchronization. Output ONLY repaired files using strict SEARCH/REPLACE format."
            )

            repair_response = self.llm.generate(repair_prompt, force_cloud=True, slow=True)
            new_files = self._write_files(repair_response)
            files_context.update(new_files)

            success, current_error = self._execute_with_critic(contract, files_context, target_test)

        if success:
            # 🚨 NEW: Distill the successful self-healing repair
            self.distiller.save_golden_record(repair_prompt, repair_response)
            
            for filename, code in files_context.items():
                self.memory.store_repair_context(current_error, code, filename)

        self.git.commit(success)
        return success

    def run(self, prompt: str):
        # 🚨 Phase 0: Explore the Workspace
        repo_context = self.explorer.investigate(prompt)

        log.info("📐 [Engine] Generating interface contract...")
        contract = self._generate_contract(prompt, repo_context)

        log.info("🔄 [Coder] Generating implementation from contract...")
        code_prompt = (
            f"Repository Context:\n{repo_context}\n\n"
            f"Implement this feature conforming STRICTLY to the interface contract:\n{contract}\n\n"
            f"CRITICAL RULES:\n"
            f"1. Output using EXACTLY the SEARCH/REPLACE block format.\n"
            f"2. Leave '<<<< SEARCH' empty if creating a new file, otherwise use exact existing lines.\n"
            f"3. No conversational text. Feature:\n{prompt}"
        )
        code_response = self.llm.generate(code_prompt)
        files = self._write_files(code_response)
        
        if not files:
            log.warning("⚠️ Escalating code generation to Cloud...")
            code_response = self.llm.generate(code_prompt, force_cloud=True, slow=True)
            files = self._write_files(code_response)
            if not files:
                log.error("🛑 [Engine] Fatal: Failed to generate source files.")
                return

        log.info("🧪 [Coder] Writing contract-aligned test suite...")
        file_context = "\n".join([f"FILE: {k}\n{v}" for k, v in files.items()])
        test_prompt = (
            f"Repository Context:\n{repo_context}\n\n"
            f"Write a pytest suite for these files conforming to this contract:\n{contract}\n\n"
            f"Files:\n{file_context}\n\n"
            f"CRITICAL RULES:\n"
            f"1. Output using the SEARCH/REPLACE block format.\n"
            f"2. Leave '<<<< SEARCH' empty if creating new test files.\n"
            f"3. Save inside 'tests/' directory.\n"
            f"4. No conversational text."
        )
        test_response = self.llm.generate(test_prompt, slow=True)
        test_files = self._write_files(test_response)

        if not test_files:
            log.warning("⚠️ Escalating test generation to Cloud...")
            test_response = self.llm.generate(test_prompt, force_cloud=True, slow=True)
            test_files = self._write_files(test_response)
            if not test_files:
                log.error("🛑 [TDD] Fatal: Failed to generate test files.")
                return

        target_test_file = next((f for f in test_files.keys() if f.startswith("tests/")), None)
        all_files = {**files, **test_files}

        success, error_output = self._execute_with_critic(contract, all_files, target_test_file)

        if not success:
            return self.resolve_error(error_output, all_files, target_test_file, contract)

        log.info("✅ [TDD] Green: All targeted tests passed!")
        
        # 🚨 NEW: Distill the knowledge from this successful run
        golden_instruction = f"Repository Context:\n{repo_context}\n\nFeature:\n{prompt}"
        golden_response = test_response if "==== REPLACE" in test_response else code_response
        self.distiller.save_golden_record(golden_instruction, golden_response)
        
        for filename, code in all_files.items():
            self.memory.store_repair_context("Initial TDD Run", code, filename)
            
        self.git.commit(success)
