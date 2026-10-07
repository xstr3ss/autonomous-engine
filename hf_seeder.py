import uuid
import json
from datasets import load_dataset
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

print("📚 [Hugging Face] Downloading CodeAlpaca dataset...")
# Load a lightweight dataset of code instructions and outputs
dataset = load_dataset("sahil2801/CodeAlpaca-20k", split="train")

client = QdrantClient(path="./qdrant_data")
points = []

print("💉 [Hugging Face] Filtering and processing 50 base-level fixes...")
# Grab the first 50 entries to establish a baseline without bloating storage
for i in range(40):
    row = dataset[i]
    # We map the dataset's 'instruction' to our error signature, and 'output' to the patch
    points.append(
        PointStruct(
            id=uuid.uuid4().hex,
            vector=[0.0] * 384,
            payload={
                "error_signature": row['instruction'],
                "patch": json.dumps({"auto_generated.py": row['output']})
            }
        )
    )

client.upsert(collection_name="bug_fixes", points=points)
client.close()

print("✅ [Hugging Face] Base-level knowledge injected into Qdrant!")
