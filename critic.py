import logging
from llm import LLMClient

log = logging.getLogger("fable.critic")

class CriticAgent:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def review(self, contract: str, files_context: dict) -> tuple[bool, str]:
        log.info("🕵️ [Critic] Static analysis & contract validation...")
        code_context = "\n".join([f"FILE: {k}\n{v}" for k, v in files_context.items()])
        critic_prompt = (
            f"You are an elite Code Critic.\n"
            f"Review these files against this contract:\n{contract}\n\n"
            f"Files:\n{code_context}\n\n"
            f"CRITICAL RULES:\n"
            f"1. Check for valid Python syntax and exact contract signature matches.\n"
            f"2. Check that the tests are correctly importing the functions.\n"
            f"3. If it looks perfectly executable, output ONLY the exact word: APPROVED\n"
            f"4. If there is a hallucination, syntax error, or mismatch, output: REJECTED: <short reason why>"
        )
        # The Critic always uses the Cloud model for maximum intelligence
        response = self.llm.generate(critic_prompt, force_cloud=True).strip()
        
        if response.startswith("APPROVED"):
            return True, ""
        return False, response
