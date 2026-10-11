with open("chat.py", "r", encoding="utf-8") as f:
    code = f.read()

new_func = '''def get_valid_model():
    """Dynamically fetch available models from Groq to prevent deprecation crashes."""
    if not groq_api_key: return "unknown"
    try:
        headers = {"Authorization": f"Bearer {groq_api_key}"}
        resp = requests.get("https://api.groq.com/openai/v1/models", headers=headers).json()
        models = [m["id"] for m in resp.get("data", [])]
        
        valid_models = [m for m in models if "guard" not in m.lower() and "whisper" not in m.lower() and "vision" not in m.lower() and "canopylabs" not in m.lower()]
        
        # Look for current Groq models (GPT-OSS or Qwen)
        for target in ["gpt-oss-20b", "qwen3.8", "gpt-oss"]:
            for m in valid_models:
                if target in m.lower(): return m
                
        return valid_models[0] if valid_models else "openai/gpt-oss-20b"
    except Exception as e:
        console.print(f"[dim red]Model discovery failed: {e}[/]")
        return "openai/gpt-oss-20b"'''

import re
code = re.sub(r'def get_valid_model\(\):.*?return "llama3-8b-8192"\n', new_func + '\n', code, flags=re.DOTALL)
# One more safety catch just in case it was hardcoded elsewhere in the file
code = code.replace('"llama-3.1-8b-instant"', 'ACTIVE_MODEL')

with open("chat.py", "w", encoding="utf-8") as f:
    f.write(code)

print("✅ Auto-Discovery updated with 2026 active models!")
