#!/usr/bin/env python3
"""
knowledge_graph.py — Unified Knowledge Layer (LanceDB + NetworkX)

Combines vector embeddings with a relationship graph for
semantic search + structured reasoning across the hive.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("KnowledgeGraph")

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    from modules.memory.vector_store import VectorStore
except ImportError:
    VectorStore = None

try:
    from modules.memory.graph_store import GraphStore
except ImportError:
    GraphStore = None


class KnowledgeGraph:
    """
    Unified knowledge layer combining vector similarity (LanceDB)
    with relationship traversal (NetworkX).
    """

    def __init__(self, base_path: str = "./data/knowledge"):
        self.base = Path(base_path)
        self.base.mkdir(parents=True, exist_ok=True)

        self.vectors = (VectorStore(str(self.base / "vectors"))
                        if VectorStore else None)
        self.graph = (GraphStore(str(self.base / "graph.json"))
                      if GraphStore else None)

        if self.vectors:
            self.vectors.create_table()
        logger.info(f"KnowledgeGraph initialized at {self.base}")

    def add_knowledge(self, id: str, text: str, vector: List[float],
                      relations: Optional[List[Dict]] = None,
                      metadata: str = ""):
        """
        Add a knowledge entry:
          - vector → LanceDB for similarity search
          - relations → NetworkX for structured traversal
        """
        if self.vectors:
            self.vectors.add(id, text, vector, metadata)
        if self.graph:
            self.graph.add_node(id, text=text, metadata=metadata)
            for rel in (relations or []):
                self.graph.add_edge(id, rel["target"],
                                    relation=rel.get("type", "related"))

    def query(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Unified query interface (used by P2P mesh).

        payload:
          - "vector": List[float] → similarity search
          - "text": str → graph text search
          - "node": str → get node + neighbors
        """
        results: Dict[str, Any] = {}

        if "vector" in payload and self.vectors:
            results["similar"] = self.vectors.search(
                payload["vector"], payload.get("top_k", 5))

        if "text" in payload and self.graph:
            nodes = self.graph.search(payload["text"])
            results["graph_matches"] = [
                {"id": n, **self.graph.get_node(n)}
                for n in nodes if self.graph.get_node(n)
            ]

        if "node" in payload and self.graph:
            node_data = self.graph.get_node(payload["node"])
            neighbors = self.graph.get_neighbors(payload["node"])
            results["node"] = node_data
            results["neighbors"] = neighbors

        return results

    def save(self):
        if self.graph:
            self.graph.save()
        logger.info("Knowledge graph saved")

    def stats(self) -> Dict[str, Any]:
        s: Dict[str, Any] = {}
        if self.vectors:
            s["vectors"] = self.vectors.count()
        if self.graph:
            s.update(self.graph.stats())
        return s
