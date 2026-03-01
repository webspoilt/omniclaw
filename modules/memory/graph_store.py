#!/usr/bin/env python3
"""
graph_store.py — NetworkX-based knowledge graph persistence.

Stores relationships between entities (files, errors, fixes, modules)
and persists to JSON for cross-session continuity.
"""

import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

try:
    import networkx as nx
    HAS_NX = True
except ImportError:
    HAS_NX = False

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("GraphStore")


class GraphStore:
    """NetworkX graph with JSON persistence."""

    def __init__(self, path: str = "./data/knowledge_graph.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if HAS_NX:
            self.graph = nx.DiGraph()
            if self.path.exists():
                self._load()
        else:
            logger.warning("networkx not installed — graph disabled")
            self.graph = None

    def _load(self):
        try:
            data = json.loads(self.path.read_text())
            self.graph = nx.node_link_graph(data)
            logger.info(f"Loaded graph: {self.graph.number_of_nodes()} nodes, "
                        f"{self.graph.number_of_edges()} edges")
        except Exception as e:
            logger.error(f"Graph load failed: {e}")

    def save(self):
        if not self.graph:
            return
        try:
            data = nx.node_link_data(self.graph)
            self.path.write_text(json.dumps(data, indent=2))
            logger.info("Graph saved")
        except Exception as e:
            logger.error(f"Graph save failed: {e}")

    def add_node(self, node_id: str, **attrs):
        if self.graph is not None:
            self.graph.add_node(node_id, **attrs)

    def add_edge(self, src: str, dst: str, **attrs):
        if self.graph is not None:
            self.graph.add_edge(src, dst, **attrs)

    def get_neighbors(self, node_id: str) -> List[str]:
        if self.graph and node_id in self.graph:
            return list(self.graph.neighbors(node_id))
        return []

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        if self.graph and node_id in self.graph:
            return dict(self.graph.nodes[node_id])
        return None

    def search(self, query: str) -> List[str]:
        """Simple label-based search across nodes."""
        if not self.graph:
            return []
        results = []
        q = query.lower()
        for n, data in self.graph.nodes(data=True):
            if q in str(n).lower() or q in str(data).lower():
                results.append(n)
        return results[:20]

    def stats(self) -> Dict[str, int]:
        if not self.graph:
            return {"nodes": 0, "edges": 0}
        return {"nodes": self.graph.number_of_nodes(),
                "edges": self.graph.number_of_edges()}
