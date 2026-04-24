"""
Knowledge Graph interface using ChromaDB for vector storage of past simulations.
"""

import hashlib
import logging
from typing import List, Optional

import chromadb
from chromadb.config import Settings

from .models import SimulationResult

logger = logging.getLogger(__name__)


class KnowledgeGraph:
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.client = chromadb.Client(
            Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=persist_directory,
            )
        )
        self.collection = self.client.get_or_create_collection(
            name="simulations",
            metadata={"hnsw:space": "cosine"},
        )

    def store(self, result: SimulationResult):
        """Store a simulation result with an embedding (derived from text)."""
        text = f"Context: {result.context}\nOutput: {result.output.get('aggregated', '')}"
        doc_id = hashlib.sha256(text.encode()).hexdigest()[:16]
        metadata = {
            "context": result.context,
            "num_agents": result.output.get("num_agents", 0),
            "successful": result.output.get("successful", 0),
            "audit_passed": result.audit.passed,
            "audit_score": result.audit.score,
        }
        self.collection.upsert(
            documents=[text],
            metadatas=[metadata],
            ids=[doc_id],
        )
        logger.info(f"Stored simulation {doc_id}")

    def query_similar(self, context: str, top_k: int = 5) -> List[str]:
        """Return similar past simulation texts."""
        results = self.collection.query(query_texts=[context], n_results=top_k)
        if results["documents"] and len(results["documents"]) > 0:
            return results["documents"][0]  # list of documents
        return []
