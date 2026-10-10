import json
import os
import requests
import re
from dotenv import load_dotenv
from bug_resolution_store import BugResolutionStore
from docker_sandbox import CodeSandbox
from tier0_parser import Tier0Parser
from diff_engine import DiffEngine
from repo_indexer import WorkspaceGraph

load_dotenv()

class SelfHealingEngine:
    def __init__(self):
        self.memory = BugResolutionStore()
        self.sandbox = CodeSandbox()
        self.parser = Tier0Parser()
        self.graph = WorkspaceGraph()
        
        self.ollama_url = "http://localhost:11434/api/generate"
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.groq_url = "https://api.groq.com/openai/v1/chat/completions"

        self.BASH_PATTERN = re.compile(r'<<<<<<< BASH\s*\n(.*?)\n>>>>>>> BASH', re.DOTALL)
        self.RAG_PATTERN = re.compile(r'<<<<<<< RAG_SEARCH\s*\n(.*?)\n>>>>>>> RAG_SEARCH', re.DOTALL)

    def _build_token_starved_context(self, error_message: str):
        mentioned = set(re.findall(r'([a-zA-Z0-9_-]+\.py)', error_message))
        if not mentioned: mentioned = {'test_server.py'}

        system_files = {'engine.py', 'auto_watcher.py', 'bug_resolution_store.py', 'docker_sandbox.py', 'tier0_parser.py', 'diff_engine.py', 'repo_indexer.py'}
        active_files = [f for f in mentioned if f not in system_files and os.path.exists(f)]

        deps = set()
        for f in active_files:
            deps.update(self.parser.find_local_dependencies(f))
        deps = [d for d in deps if d not in system_files and d not in active_files and os.path.exists(d)]

        target_file = deps[0] if deps else (active_files[0] if active_files else "server.py")
        if target_file in deps:
            deps.remove(target_file)
            active_files.append(target_file)

        context = "### FULL SOURCE FILES (TARGET FILES):\n"
        for f in active_files:
            if os.path.exists(f):
                with open(f, 'r', encoding='utf-8') as src:
                    context += f"\n--- {f} ---\n{src.read()}\n"

        if deps:
            context += "\n### DEPENDENCY SKELETAL MAPS (Signatures Only - Do not modify):\n"
            for d in deps:
                if os.path.exists(d):
                    context += f"\n--- {d} (Skeleton) ---\n{self.parser.generate_skeletal_map(d)}\n"

        return context, target_file

    def _query_model(self, prompt: str, use_cloud: bool = False) -> str:
        if use_cloud:
            headers = {"Authorization": f"Bearer {self.groq_api_key}", "Content-Type": "application/json"}
            payload = {"model": "qwen/qwen3.8-27b", "messages": [{"role": "user", "content": prompt}], "temperature": 0.1}
            try:
                resp = requests.post(self.groq_url, headers=headers, json=payload, timeout=30)
                if resp.status_code == 200: return resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            except Exception as e: print(f"⚠️ [Cloud API] Error: {e}")
            return ""
        else:
            try:
                resp = requests.post(self.ollama_url, json={"model": "qwen2.5-coder:3b", "prompt": prompt, "stream": False}, timeout=90)
                if resp.status_code == 200: return resp.json().get("response", "")
            except Exception as e: print(f"⚠️ [Local API] Error: {e}")
            return ""

    def _agentic_reasoning_loop(self, base_prompt: str, use_cloud: bool = False) -> str:
        current_prompt = base_prompt
        max_steps = 4
        
        for step in range(max_steps):
            response = self._query_model(current_prompt, use_cloud)
            
            # Tool 1: RAG Search (Semantic Vector Lookup)
            rag_matches = self.RAG_PATTERN.findall(response)
            if rag_matches:
                query = rag_matches[0].strip()
                print(f"🧠 [Agentic Tool] AI queried Context Graph: '{query}'")
                results = self.graph.semantic_search(query, limit=2)
                
                graph_output = "Found matching structural nodes:\n" if results else "No matching files found.\n"
                for res in results:
                    graph_output += f"--- {res['filepath']} (Match Score: {res['score']:.2f}) ---\n{res['skeleton']}\n\n"
                
                print(f"   -> Graph returned {len(results)} file skeletons to AI.")
                current_prompt += f"\n\n[You queried Context Graph for]: {query}\n[Graph Results]:\n{graph_output}\n\nNow, execute BASH, another RAG_SEARCH, or output the PATCH."
                continue

            # Tool 2: BASH (Terminal Explorer)
            bash_matches = self.BASH_PATTERN.findall(response)
            if bash_matches:
                cmd = bash_matches[0].strip()
                print(f"🔍 [Agentic Tool] AI executed BASH command: {cmd}")
                success, bash_output = self.sandbox.run_bash(cmd)
                
                if len(bash_output) > 1500: bash_output = bash_output[:1500] + "\n...[TRUNCATED]"
                if not bash_output: bash_output = "[Command executed successfully with no output]"
                
                print("   -> Terminal result returned to AI context.")
                current_prompt += f"\n\n[You executed BASH]: {cmd}\n[Terminal Output]:\n{bash_output}\n\nNow, execute another BASH command, a RAG_SEARCH, or output the PATCH."
                continue
                
            return response

    def resolve_error(self, error_message: str) -> bool:
        print(f"\n🚨 [Engine] Detected failure. Initializing Multi-Tool Agentic Loop...")
        context, target_file = self._build_token_starved_context(error_message)
        max_retries = 3
        failed_history = ""

        base_prompt_template = f"""You are an elite Autonomous Software Repair Agent.
Error: {error_message}

Context: {context}

TARGET FILE TO MODIFY: {target_file}

CRITICAL RULES:
1. NO CONVERSATION. NO EXPLANATIONS.
2. You have THREE options. Choose ONLY ONE per response.

OPTION 1: SEMANTIC SEARCH (Find a function/class across the entire repo without knowing the filename)
<<<<<<< RAG_SEARCH
database connection utility
>>>>>>> RAG_SEARCH

OPTION 2: EXPLORE (Run a terminal command)
<<<<<<< BASH
cat requirements.txt
>>>>>>> BASH

OPTION 3: PATCH (Fix the code in {target_file})
<<<<<<< SEARCH
    return "bad_code"
=======
    return "good_code"
>>>>>>> REPLACE

WARNING: For PATCH, the SEARCH block MUST match the file exactly. Do not use markdown blocks around the tags.
"""

        for attempt in range(max_retries):
            print(f"🔄 [Agent Loop] Attempt {attempt + 1} of {max_retries} (Local SLM)...")
            prompt = base_prompt_template + f"\nPrevious Failed Attempts:\n{failed_history}"
            
            raw_diff = self._agentic_reasoning_loop(prompt, use_cloud=False)
            blocks = DiffEngine.parse_diff_blocks(raw_diff)

            if not blocks:
                print("❌ [Engine] No valid SEARCH/REPLACE blocks parsed.")
                failed_history += f"\nAttempt {attempt + 1}: Model did not produce valid SEARCH/REPLACE blocks."
                continue

            with open(target_file, "r", encoding="utf-8") as f: backup = f.read()
            applied, patch_msg = DiffEngine.patch_file(target_file, blocks)
            
            if not applied:
                print(f"❌ [Diff Engine] Patch failed to apply: {patch_msg}")
                failed_history += f"\nAttempt {attempt + 1}: Diff failed to apply."
                continue

            print(f"🧪 [CI/CD] Validating patch on {target_file} inside Persistent Sandbox...")
            success, output = self.sandbox.run_bash(f"pytest test_server.py") 

            if success:
                print(f"✅ [Engine] Fix verified by Sandbox! Changes saved directly to {target_file}.")
                # Re-index the workspace since code changed!
                self.graph.index_workspace()
                return True
            else:
                print(f"❌ [CI/CD] Sandbox rejected patch.")
                with open(target_file, "w", encoding="utf-8") as f: f.write(backup)
                failed_history += f"\nAttempt {attempt + 1} failed Sandbox test."

        print("🚀 [Tier 2] Escalating to Groq Cloud Engine with Agentic capabilities...")
        cloud_prompt = base_prompt_template + f"\nPrevious Local SLM Failures to avoid:\n{failed_history}"
        raw_cloud_diff = self._agentic_reasoning_loop(cloud_prompt, use_cloud=True)
        cloud_blocks = DiffEngine.parse_diff_blocks(raw_cloud_diff)

        if cloud_blocks:
            with open(target_file, "r", encoding="utf-8") as f: backup = f.read()
            applied, patch_msg = DiffEngine.patch_file(target_file, cloud_blocks)
            if applied:
                success, output = self.sandbox.run_bash(f"pytest test_server.py")
                if success:
                    print(f"✅ [Tier 2] Cloud fix verified! Changes written to {target_file}.")
                    self.graph.index_workspace()
                    return True
                else:
                    with open(target_file, "w", encoding="utf-8") as f: f.write(backup)
                    print("❌ [Tier 2] Cloud fix failed Sandbox verification.")
            else:
                print(f"❌ [Tier 2] Cloud diff failed to apply.")
        
        print("❌ [Engine] All local and cloud repair tiers exhausted.")
        return False

    def shutdown(self):
        self.memory.close()
        self.sandbox.shutdown()

if __name__ == "__main__":
    pass
