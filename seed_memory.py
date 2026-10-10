import uuid
import json
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance

print("🌱 [Seeder] Booting up memory injection protocol...")

# Connect to local Qdrant
client = QdrantClient(path="./qdrant_data")

# Ensure collection exists
if not client.collection_exists("bug_fixes"):
    client.create_collection(
        collection_name="bug_fixes",
        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
    )

# Define our synthetic training data (Known Bugs -> Known Fixes)
training_data = [
    {
        "error": "IndentationError: expected an indented block",
        "patch": {"main.py": "def hello_world():\n    print('Hello World')"}
    },
    {
        "error": "ZeroDivisionError: division by zero",
        "patch": {"math_utils.py": "def safe_divide(a, b):\n    if b == 0:\n        return 0\n    return a / b"}
    },
    {
        "error": "ImportError: No module named 'requests'",
        "patch": {"requirements.txt": "requests==2.31.0\n"}
    }
]

print(f"💉 [Seeder] Injecting {len(training_data)} synthetic fixes into vector memory...")

points = []
for item in training_data:
    points.append(
        PointStruct(
            id=uuid.uuid4().hex,
            vector=[0.0] * 384, # Placeholder math vector
            payload={
                "error_signature": item["error"],
                "patch": json.dumps(item["patch"], indent=2)
            }
        )
    )

client.upsert(
    collection_name="bug_fixes",
    points=points
)
client.close()

print("✅ [Seeder] Memory bank successfully populated!")
