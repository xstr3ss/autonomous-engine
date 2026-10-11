with open("engine.py", "r", encoding="utf-8") as f:
    code = f.read()

# 1. Give Groq 120 seconds to do heavy quantitative reasoning
code = code.replace("timeout=30", "timeout=120")

# 2. Scrub the local prompt of the old enterprise_db hallucination loop
import re
code = re.sub(r'from enterprise_db import.*?\n', '# Implement the requested logic here\n', code, flags=re.DOTALL)
code = re.sub(r'connection = establish_secure_connection\(\).*?\n', '', code, flags=re.DOTALL)

with open("engine.py", "w", encoding="utf-8") as f:
    f.write(code)

print("✅ Engine patched: API timeout increased to 120s and prompt cache cleared.")
