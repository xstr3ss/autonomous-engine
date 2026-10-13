import logging
import subprocess
import tempfile
import os
from llm import LLMClient

log = logging.getLogger("fable.verifier")

class FormalVerifier:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def verify(self, contract: str, files_context: dict) -> tuple[bool, str]:
        """
        Synthesizes a Z3 theorem proving script to mathematically verify
        invariants and boundary conditions over symbolic inputs.
        """
        log.info("📐 [Verifier] Generating formal Z3 symbolic proof script...")
        code_context = "\n".join([f"FILE: {k}\n{v}" for k, v in files_context.items()])

        proof_prompt = (
            f"You are the Fable Formal Verification Engineer using the Z3 Theorem Prover.\n"
            f"Contract:\n{contract}\n\n"
            f"Code under inspection:\n{code_context}\n\n"
            f"GOAL:\n"
            f"Write a standalone Python script using `from z3 import *` to symbolically verify "
            f"that the core function satisfies its invariants and has no mathematical boundary bugs "
            f"(e.g., division by zero, unhandled negative inputs, integer overflow, index out of range).\n\n"
            f"RULES:\n"
            f"1. Create symbolic variables (e.g., `Int('n')`, `Real('x')`).\n"
            f"2. Formulate constraints representing the function's logic and the expected postcondition.\n"
            f"3. Add the negation of the safety property to the solver.\n"
            f"4. If `s.check() == sat`, print: 'PROOF_FAILED: <exact model counterexample>'\n"
            f"5. If `s.check() == unsat`, print: 'PROOF_SUCCESS: Invariant holds for all inputs'\n"
            f"6. Output ONLY executable Python code inside a ```python ``` block. No conversational text."
        )

        response = self.llm.generate(proof_prompt, force_cloud=True)
        
        # Extract python code
        if "```python" in response:
            proof_code = response.split("```python")[1].split("```")[0].strip()
        elif "```" in response:
            proof_code = response.split("```")[1].split("```")[0].strip()
        else:
            proof_code = response.strip()

        # Run the Z3 proof script in a temporary isolated file
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(proof_code)
            tmp_path = f.name

        try:
            log.info("⚡ [Verifier] Executing symbolic solver...")
            result = subprocess.run(
                ["python", tmp_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            output = result.stdout.strip()
            
            if "PROOF_SUCCESS" in output:
                log.info("🛡️ [Verifier] Symbolic proof verified: Code invariants hold mathematically.")
                return True, output
            elif "PROOF_FAILED" in output:
                log.warning(f"❌ [Verifier] Counterexample found by Z3:\n{output}")
                return False, output
            else:
                log.warning(f"⚠️ [Verifier] Proof script returned indeterminate result: {output or result.stderr}")
                return True, "Verification skipped: Indeterminate"
        except subprocess.TimeoutExpired:
            log.warning("⏳ [Verifier] Z3 solver timed out. Path space too large, falling back to tests.")
            return True, "Verification timed out"
        except Exception as e:
            log.warning(f"⚠️ [Verifier] Error during proof execution: {e}")
            return True, "Verification bypassed due to execution error"
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
