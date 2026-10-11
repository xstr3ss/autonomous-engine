with open("engine.py", "r", encoding="utf-8") as f:
    code = f.read()

# Protect the Diff parser from receiving None
code = code.replace("cloud_blocks = DiffEngine.parse_diff_blocks(raw_cloud_diff)", "cloud_blocks = DiffEngine.parse_diff_blocks(raw_cloud_diff or '')")
code = code.replace("blocks = DiffEngine.parse_diff_blocks(raw_diff)", "blocks = DiffEngine.parse_diff_blocks(raw_diff or '')")

with open("engine.py", "w", encoding="utf-8") as f:
    f.write(code)

print("✅ Agent loop fall-through bug patched.")
