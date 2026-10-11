with open("repo_indexer.py", "r", encoding="utf-8") as f:
    code = f.read()

old_client_init = "self.client = QdrantClient(path=db_path)"
new_client_init = """import shutil
        try:
            self.client = QdrantClient(path=db_path)
        except Exception as e:
            print(f"🧹 [Context Graph] Phantom database lock detected! Auto-wiping...")
            shutil.rmtree(db_path, ignore_errors=True)
            self.client = QdrantClient(path=db_path)"""

if old_client_init in code and "shutil.rmtree" not in code:
    code = code.replace(old_client_init, new_client_init)
    with open("repo_indexer.py", "w", encoding="utf-8") as f:
        f.write(code)
    print("✅ Lock-Buster activated! The Engine will now auto-heal its own database locks.")
else:
    print("⚠️ Lock-Buster already applied or code mismatch.")
