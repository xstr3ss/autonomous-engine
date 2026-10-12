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
        # Connect to local Qdrant (or in-memory if URL is missing)
        self.qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.client = QdrantClient(url=self.qdrant_url)
        
        # Local, token-free embeddings via Ollama
        self.ollama_url = os.getenv("OLLAMA_EMBED_URL", "http://localhost:11434/api/embeddings")
        self.embed_model = os.getenv("EMBED_MODEL", "nomic-embed-text") 
        
        self._ensure_collection()

    def _ensure_collection(self):
        """Bootstraps the collection using the dimension size of nomic-embed-text (768)."""
        if not self.client.collection_exists(self.collection_name):
            log.info(f"🧠 [Memory] Bootstrapping new Qdrant collection: {self.collection_name}")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE),
            )

    def _get_embedding(self, text: str) -> List[float]:
        """Fetches embeddings from the local Ollama instance."""
        try:
            payload = {"model": self.embed_model, "prompt": text}
            res = requests.post(self.ollama_url, json=payload, timeout=10)
            res.raise_for_status()
            return res.json().get("embedding", [])
        except Exception as e:
            log.error(f"❌ [Memory] Embedding failed (Is Ollama running?): {e}")
            return []

    def store_repair_context(self, error_signature: str, successful_code: str, file_path: str):
        """Indexes a successful TDD repair so the agent doesn't have to relearn it."""
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
        """Fetches past successful repairs for similar errors to constrain the context window."""
        vector = self._get_embedding(current_error)
        if not vector:
            return []

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=vector,
            limit=limit
        )
        
        # Only return highly confident matches to prevent hallucination cascades
        return [hit.payload for hit in results if hit.score > 0.75]
