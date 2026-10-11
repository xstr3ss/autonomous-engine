import re

with open("engine.py", "r", encoding="utf-8") as f:
    code = f.read()

# 1. Fix the NoneType error in the regex context builder
code = code.replace("def _build_token_starved_context(self, error_message: str):", "def _build_token_starved_context(self, error_message: str):\n        error_message = str(error_message) if error_message else ''")

# 2. Give the agent more turns to investigate files (4 -> 6)
code = code.replace("max_steps = 4", "max_steps = 6")

# 3. Idiot-proof the prompt (remove the word "PATCH" which confused the local SLM)
new_prompt = '''        base_prompt_template = f"""You are an elite Autonomous Software Repair Agent.
Error: {error_message}

TARGET FILE: {target_file}

Context: {context}

CRITICAL RULES:
1. NO CONVERSATION. Output ONLY ONE tool block per response.

To search the codebase, use this exact format:
<<<<<<< RAG_SEARCH
your query
>>>>>>> RAG_SEARCH

To run a terminal command, use this exact format:
<<<<<<< BASH
cat {target_file}
>>>>>>> BASH

To patch the file, use this exact format (DO NOT use markdown blocks like ```):
<<<<<<< SEARCH
    connection = connect_to_db()
=======
    from enterprise_db import establish_secure_connection
    connection = establish_secure_connection()
>>>>>>> REPLACE
"""'''

code = re.sub(r'        base_prompt_template = f"""You are an elite.*?>>>>>>> REPLACE\n"""', new_prompt, code, flags=re.DOTALL)

with open("engine.py", "w", encoding="utf-8") as f:
    f.write(code)

print("✅ Engine patched: 6-step loop active, NoneType bug fixed, prompt simplified.")
