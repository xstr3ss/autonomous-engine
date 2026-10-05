import json
from qdrant_client import QdrantClient

def export_qdrant_to_jsonl():
    print("📥 [Data Exporter] Connecting to Qdrant memory...")
    client = QdrantClient(path="./qdrant_storage")
    
    # Scroll through all records in the database collection
    records, _ = client.scroll(
        collection_name="bug_fixes",
        limit=100,
        with_payload=True
    )
    
    output_file = "finetune_dataset.jsonl"
    print(f"📦 [Data Exporter] Found {len(records)} successful fixes. Formatting for Unsloth...")
    
    with open(output_file, 'w') as f:
        for record in records:
            payload = record.payload
            
            # The standard Alpaca format for fine-tuning LLMs
            dataset_row = {
                "instruction": "Fix the following error in the codebase.",
                "input": payload.get("error_message", ""),
                "output": payload.get("applied_patch", "")
            }
            # Write exactly one JSON object per line
            f.write(json.dumps(dataset_row) + '\n')
            
    print(f"✅ [Data Exporter] Successfully exported to {output_file}")
    
if __name__ == "__main__":
    export_qdrant_to_jsonl()
