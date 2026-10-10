import json
from qdrant_client import QdrantClient

print("📦 [Exporter] Connecting to Qdrant Vector Bank...")
try:
    client = QdrantClient(path="./qdrant_data")
    
    if not client.collection_exists("bug_fixes"):
        print("⚠️ [Exporter] No memory found. Nothing to export.")
        exit()
        
    records, _ = client.scroll(
        collection_name="bug_fixes",
        limit=10000  # Pull all stored memories
    )
    client.close()
    
    if not records:
        print("⚠️ [Exporter] Memory bank is empty.")
        exit()
        
    print(f"📊 [Exporter] Found {len(records)} memorized fixes. Converting to JSONL...")
    
    export_file = "finetuning_dataset.jsonl"
    with open(export_file, "w", encoding="utf-8") as f:
        for record in records:
            error = record.payload.get("error_signature", "")
            patch = record.payload.get("patch", "")
            
            # Standard instruction-tuning format for Llama/Qwen/Mistral
            dataset_row = {
                "messages": [
                    {"role": "system", "content": "You are an autonomous CI/CD debugging agent. Return ONLY a valid JSON object where keys are file paths and values are file contents."},
                    {"role": "user", "content": f"A Python test failed with the following error:\n{error}"},
                    {"role": "assistant", "content": patch}
                ]
            }
            f.write(json.dumps(dataset_row) + "\n")
            
    print(f"✅ [Exporter] Success! Dataset saved to {export_file}")
    print("🚀 [Endgame] You are now ready to fine-tune your own local AI model!")

except Exception as e:
    print(f"❌ [Exporter] Error: {e}")
