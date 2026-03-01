#!/usr/bin/env python3
"""
vector_store.py — LanceDB wrapper for embedding storage and similarity search.

Used by the knowledge graph and P2P knowledge queries.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("VectorStore")

try:
    import lancedb
    HAS_LANCE = True
except ImportError:
    HAS_LANCE = False

try:
    import numpy as np
    HAS_NP = True
except ImportError:
    HAS_NP = False


class VectorStore:
    """LanceDB-backed vector store for embeddings."""

    def __init__(self, db_path: str = "./data/vectors"):
        self.db_path = Path(db_path)
        self.db_path.mkdir(parents=True, exist_ok=True)
        self.db = None
        self.table = None
        if HAS_LANCE:
            try:
                self.db = lancedb.connect(str(self.db_path))
                logger.info(f"LanceDB connected: {self.db_path}")
            except Exception as e:
                logger.error(f"LanceDB init failed: {e}")
        else:
            logger.warning("lancedb not installed — using in-memory fallback")
            self._fallback: List[dict] = []

    def create_table(self, name: str = "embeddings",
                     dim: int = 384) -> bool:
        """Create or open a table."""
        if not self.db:
            return False
        try:
            tables = self.db.table_names()
            if name in tables:
                self.table = self.db.open_table(name)
            else:
                import pyarrow as pa
                schema = pa.schema([
                    pa.field("id", pa.string()),
                    pa.field("text", pa.string()),
                    pa.field("vector", pa.list_(pa.float32(), dim)),
                    pa.field("metadata", pa.string()),
                ])
                self.table = self.db.create_table(name, schema=schema)
            return True
        except Exception as e:
            logger.error(f"Table creation: {e}")
            return False

    def add(self, id: str, text: str, vector: List[float],
            metadata: str = ""):
        """Insert a vector with metadata."""
        entry = {"id": id, "text": text, "vector": vector,
                 "metadata": metadata}
        if self.table:
            try:
                self.table.add([entry])
            except Exception as e:
                logger.error(f"Add failed: {e}")
        else:
            self._fallback.append(entry)

    def search(self, query_vector: List[float],
               top_k: int = 5) -> List[Dict[str, Any]]:
        """Similarity search."""
        if self.table:
            try:
                results = (self.table.search(query_vector)
                           .limit(top_k).to_list())
                return results
            except Exception as e:
                logger.error(f"Search failed: {e}")
                return []
        else:
            # Fallback: brute-force cosine similarity
            if not HAS_NP or not self._fallback:
                return []
            qv = np.array(query_vector)
            scored = []
            for entry in self._fallback:
                ev = np.array(entry["vector"])
                cos = np.dot(qv, ev) / (np.linalg.norm(qv) * np.linalg.norm(ev) + 1e-9)
                scored.append({**entry, "_distance": 1 - cos})
            scored.sort(key=lambda x: x["_distance"])
            return scored[:top_k]

    def count(self) -> int:
        if self.table:
            try:
                return self.table.count_rows()
            except Exception:
                return 0
        return len(self._fallback)
