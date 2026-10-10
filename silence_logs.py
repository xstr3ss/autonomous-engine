with open("repo_indexer.py", "r") as f:
    code = f.read()

stealth_mode = """import os
# Suppress HuggingFace warnings before they load
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import logging
# Muzzle the scary HTTP Request logs
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
"""

if "HF_HUB_DISABLE_SYMLINKS_WARNING" not in code:
    code = stealth_mode + "\n" + code
    with open("repo_indexer.py", "w") as f:
        f.write(code)

print("🥷 Stealth Mode activated! HTTP logs are muzzled.")
