import os
import logging
import requests
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
import uuid

log = logging.getLogger("fable.memory")

class VectorMemory:
    def __init__(self, collection_name: str = "fable_ast_memory"):
        self.collection_name = collection_name
        self.qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.client = QdrantClient(url=self.qdrant_url)
        
        self.ollama_url = os.getenv("OLLAMA_EMBED_URL", "http://localhost:11434/api/embeddings")
        self.embed_model = os.getenv("EMBED_MODEL", "nomic-embed-text") 
        
        self._ensure_collection()

    def _ensure_collection(self):
        if not self.client.collection_exists(self.collection_name):
            log.info(f"🧠 [Memory] Bootstrapping new Qdrant collection: {self.collection_name}")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE),
            )

    def _get_embedding(self, text: str) -> List[float]:
        try:
            payload = {"model": self.embed_model, "prompt": text}
            res = requests.post(self.ollama_url, json=payload, timeout=10)
            res.raise_for_status()
            return res.json().get("embedding", [])
        except Exception as e:
            log.error(f"❌ [Memory] Embedding failed (Is Ollama running?): {e}")
            return []

    def store_repair_context(self, error_signature: str, successful_code: str, file_path: str):
        text_to_embed = f"Error: {error_signature}\nFix: {successful_code}"
        vector = self._get_embedding(text_to_embed)
        
        if not vector:
            return

        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={
                "error_signature": error_signature,
                "file_path": file_path,
                "code_snapshot": successful_code,
                "type": "successful_repair"
            }
        )
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )
        log.info("💾 [Memory] Repair sequence permanently indexed in Qdrant.")

    def recall_similar_errors(self, current_error: str, limit: int = 1) -> List[Dict[str, Any]]:
        vector = self._get_embedding(current_error)
        if not vector:
            return []

        # Use the modern query_points API
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=vector,
            limit=limit
        ).points
        
        return [hit.payload for hit in results if hit.score > 0.75]
