import re

with open("engine.py", "r") as f:
    code = f.read()

new_prompt = '''        base_prompt_template = f"""You are an elite Autonomous Software Repair Agent.
Error: {error_message}

Context: {context}

TARGET FILE TO MODIFY: {target_file}

CRITICAL RULES:
1. NO CONVERSATION. NO EXPLANATIONS. 
2. You have two options: BASH or PATCH. Choose ONE.

OPTION 1: EXPLORE (Run a terminal command)
<<<<<<< BASH
cat secrets.env
>>>>>>> BASH

OPTION 2: PATCH (Fix the code in {target_file})
<<<<<<< SEARCH
    # BUG: We are missing the API key!
    return "missing_key"
=======
    return "sk-12345-real-key"
>>>>>>> REPLACE

WARNING: For PATCH, the SEARCH block MUST match the file exactly. Do not use markdown blocks (```) around the special <<<<<<< tags.
"""'''

code = re.sub(r'        base_prompt_template = f"""You are an elite.*?>>>>>>> REPLACE\n"""', new_prompt, code, flags=re.DOTALL)

with open("engine.py", "w") as f:
    f.write(code)

print("✅ Agent Prompts hardened with Few-Shot Examples!")
