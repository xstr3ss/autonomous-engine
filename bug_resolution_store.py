import uuid
import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

class BugResolutionStore:
    def __init__(self, collection_name="bug_fixes", storage_path="./qdrant_storage"):
        self.collection_name = collection_name
        self.storage_path = storage_path
        
        os.makedirs(self.storage_path, exist_ok=True)
        self.client = QdrantClient(path=self.storage_path)
        
        print("Loading embedding model (this may take a moment on first run)...")
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
        self.vector_size = self.encoder.get_embedding_dimension()
        
        self._initialize_collection()

    def _initialize_collection(self):
        collections = self.client.get_collections().collections
        exists = any(col.name == self.collection_name for col in collections)
        
        if not exists:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size, 
                    distance=Distance.COSINE
                )
            )
            print(f"Collection '{self.collection_name}' initialized successfully.")

    def store_fix(self, error_message: str, applied_patch: str, success_score: float):
        vector = self.encoder.encode(error_message).tolist()
        point_id = str(uuid.uuid4())
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "error_message": error_message,
                        "applied_patch": applied_patch,
                        "success_score": success_score
                    }
                )
            ]
        )
        print(f"Stored fix for error: '{error_message[:40]}...' | ID: {point_id}")

    def search_similar_error(self, error_message: str, limit: int = 3):
        vector = self.encoder.encode(error_message).tolist()
        
        # FIXED: Changed from .search() to .query_points()
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=vector,
            limit=limit
        )
        
        # query_points returns an object with a .points attribute
        return [
            {
                "score": hit.score,
                "error_message": hit.payload.get("error_message", ""),
                "applied_patch": hit.payload.get("applied_patch", ""),
                "success_score": hit.payload.get("success_score", 0.0)
            }
            for hit in response.points
        ]
        
    def close(self):
        """Cleanly shuts down the Qdrant connection."""
        self.client.close()

if __name__ == "__main__":
    print("\n--- Testing BugResolutionStore ---")
    store = BugResolutionStore()
    
    try:
        print("\n1. Storing a test fix...")
        store.store_fix(
            error_message="IndexError: list index out of range in data_parser.py line 42",
            applied_patch="if i < len(data_list):\n    val = data_list[i]\nelse:\n    val = None",
            success_score=1.0
        )
        
        print("\n2. Searching for similar errors...")
        search_results = store.search_similar_error("IndexError: list index out of range in config_loader.py")
        
        for res in search_results:
            print(f"\nMatch Score: {res['score']:.4f}")
            print(f"Original Error: {res['error_message']}")
            print(f"Suggested Patch:\n{res['applied_patch']}")
    finally:
        # FIXED: Ensure clean teardown so python doesn't throw closing errors
        store.close()
