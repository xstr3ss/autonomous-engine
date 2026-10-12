import logging
import subprocess
from llm import LLMClient

log = logging.getLogger("fable.explorer")

class WorkspaceExplorer:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def investigate(self, issue_description: str, max_steps: int = 4) -> str:
        log.info("🗺️ [Explorer] Analyzing repository to locate target files...")
        
        transcript = f"ISSUE TO SOLVE:\n{issue_description}\n\nExplore the workspace to find relevant files."
        
        for step in range(1, max_steps + 1):
            prompt = (
                f"You are the Fable Explorer Agent. Your goal is to gather context to solve the ISSUE.\n"
                f"Transcript so far:\n{transcript}\n\n"
                f"RULES:\n"
                f"1. To explore, output a SINGLE read-only bash command (e.g. ls, grep, cat) using EXACTLY this format:\n"
                f"COMMAND: <your bash command>\n"
                f"2. If you have found the files and read their contents, you are ready to code. Output EXACTLY:\n"
                f"DONE: <Detailed summary of the files, their current code, and what needs changing>"
            )
            
            # The Explorer requires high reasoning, so we force it to the Cloud model
            response = self.llm.generate(prompt, force_cloud=True).strip()
            
            if response.startswith("DONE:"):
                log.info("✅ [Explorer] Investigation complete. Context gathered.")
                return response.replace("DONE:", "").strip()
            
            if "COMMAND:" in response:
                # Extract the exact command
                cmd_line = [line for line in response.split("\n") if line.startswith("COMMAND:")][0]
                command = cmd_line.replace("COMMAND:", "").strip()
                
                log.info(f"🕵️ [Explorer] Step {step}/{max_steps} | Running: {command}")
                
                try:
                    proc = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=5)
                    output = proc.stdout[:2000] # Cap massive outputs so we don't blow the context window
                    if not output.strip():
                        output = "<no output>"
                except Exception as e:
                    output = f"Error executing command: {e}"
                    
                transcript += f"\n\nYOU RAN: {command}\nOUTPUT:\n{output}"
            else:
                log.warning("⚠️ [Explorer] Invalid output format. Forcing exit.")
                return "Failed to explore."
                
        log.warning("🗺️ [Explorer] Reached max exploration steps.")
        return "Exploration timed out. Proceed with limited context."
