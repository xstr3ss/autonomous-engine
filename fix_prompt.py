import re

with open("engine.py", "r") as f:
    code = f.read()

new_prompt = '''        base_prompt_template = f"""You are an elite Autonomous Software Repair Agent.
Error: {error_message}

TARGET FILE TO MODIFY: {target_file}

Context: {context}

CRITICAL RULES:
1. NO CONVERSATION. You may only output ONE of the following three tool blocks.

OPTION 1: RAG_SEARCH (Find missing utilities or functions across the codebase)
<<<<<<< RAG_SEARCH
secure connection
>>>>>>> RAG_SEARCH

OPTION 2: BASH (Explore terminal)
<<<<<<< BASH
ls -la
>>>>>>> BASH

OPTION 3: PATCH (Apply the fix to {target_file})
<<<<<<< SEARCH
    connection = connect_to_db()
=======
    from enterprise_db import establish_secure_connection
    connection = establish_secure_connection()
>>>>>>> REPLACE

WARNING: For PATCH, the SEARCH block MUST match the exact current contents of {target_file}.
"""'''

code = re.sub(r'        base_prompt_template = f"""You are an elite.*?>>>>>>> REPLACE\n"""', new_prompt, code, flags=re.DOTALL)

with open("engine.py", "w") as f:
    f.write(code)

print("✅ Prompt upgraded to the 'Clear Thought' Architecture!")
