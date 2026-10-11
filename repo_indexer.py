import os
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

import os
import hashlib
import logging
from typing import List, Dict
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from tier0_parser import Tier0Parser

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("RepoIndexer")

class WorkspaceGraph:
    """
    Builds a vectorized Code Property Graph of the entire workspace.
    Allows the AI to semantically search for functions, classes, and variables
    without loading the entire repository into its context window.
    """
    def __init__(self, db_path: str = "./qdrant_ledger_data"):
        self.collection_name = "workspace_graph"
        # Using a fast, local, zero-cost embedding model
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
        import shutil
        try:
            self.client = QdrantClient(path=db_path)
        except Exception as e:
            print(f"🧹 [Context Graph] Phantom database lock detected! Auto-wiping...")
            shutil.rmtree(db_path, ignore_errors=True)
            self.client = QdrantClient(path=db_path)
        self.parser = Tier0Parser()
        self._initialize_schema()

    def _initialize_schema(self):
        """Idempotently creates the workspace vector index."""
        if not self.client.collection_exists(collection_name=self.collection_name):
            logger.info("🌌 Initializing Global Context Graph in Qdrant...")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.encoder.get_sentence_embedding_dimension(),
                    distance=Distance.COSINE
                )
            )

    def _generate_id(self, text: str) -> str:
        """Generates a stable UUID based on the content."""
        import uuid
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, text))

    def index_workspace(self, root_dir: str = "."):
        """
        Scans all Python files, uses Tier 0 to extract structure, 
        and updates the vector database.
        """
        logger.info(f"🔍 Scanning workspace: {os.path.abspath(root_dir)}")
        points_to_upsert = []

        ignore_dirs = {'.git', '__pycache__', '.pytest_cache', 'venv', 'env', 'qdrant_ledger_data'}

        for dirpath, dirnames, filenames in os.walk(root_dir):
            dirnames[:] = [d for d in dirnames if d not in ignore_dirs]
            
            for file in filenames:
                if not file.endswith(".py"):
                    continue
                    
                filepath = os.path.join(dirpath, file)
                try:
                    # Use Tier 0 to get the skeleton of the file
                    skeleton = self.parser.generate_skeletal_map(filepath)
                    
                    if not skeleton.strip():
                        continue

                    # Vectorize the file's architectural summary
                    embedding = self.encoder.encode(skeleton).tolist()
                    point_id = self._generate_id(filepath)
                    
                    points_to_upsert.append(PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload={
                            "filepath": filepath,
                            "type": "file_skeleton",
                            "content": skeleton
                        }
                    ))
                except Exception as e:
                    logger.warning(f"Could not index {filepath}: {e}")

        if points_to_upsert:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points_to_upsert
            )
            logger.info(f"✅ Indexed {len(points_to_upsert)} structural nodes into the Context Graph.")

    def semantic_search(self, query: str, limit: int = 3) -> List[Dict]:
        """
        Allows the agent to ask questions like:
        'Where is the database connection managed?'
        """
        query_vector = self.encoder.encode(query).tolist()
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=limit
        )
        
        return [
            {"filepath": hit.payload["filepath"], "score": hit.score, "skeleton": hit.payload["content"]}
            for hit in results.points
        ]

if __name__ == "__main__":
    graph = WorkspaceGraph()
    graph.index_workspace()
    
    # Quick Test
    print("\n🧪 Testing Semantic RAG Search:")
    test_query = "database connection or configuration"
    print(f"Query: '{test_query}'")
    for res in graph.semantic_search(test_query, limit=1):
        print(f"-> Found in {res['filepath']} (Score: {res['score']:.2f})")
