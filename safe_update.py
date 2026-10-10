with open("engine.py", "r") as f:
    code = f.read()

tier2_marker = 'print("🐢 [Tier 2]'
if tier2_marker in code:
    top_half, bottom_half = code.split(tier2_marker, 1)
    prompt_start_idx = top_half.rfind('prompt =')

    if prompt_start_idx != -1:
        pre_prompt = top_half[:prompt_start_idx]
        new_prompt = '''prompt = f"Fix this code failing with the following error:\\n{error_message}\\n\\nHere is the current codebase:\\n{codebase}\\n"
        prompt += """
You must return your response EXACTLY as a valid JSON object. Do not add markdown blocks or explanations.

CRITICAL JSON STRUCTURE:
{
    "filepath.py": "ENTIRE fixed python code here",
    "requirements.txt": "package_name" 
}

RULES:
1. Fix the Python code logically to pass the tests.
2. If the error explicitly mentions a missing module or ModuleNotFoundError, you MUST include the "requirements.txt" key alongside the python file.
3. If there is no missing module, omit the "requirements.txt" key.
"""\n        '''

        new_code = pre_prompt + new_prompt + tier2_marker + bottom_half
        with open("engine.py", "w") as f:
            f.write(new_code)
        print("✅ engine.py successfully patched!")
