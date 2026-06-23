import re
from collections import defaultdict

from core.skills.registry import tool

_knowledge_store = defaultdict(list)

@tool()
def extract_entities(text: str, entity_types: str = "email,url,ip,path") -> str:
    """Extract entities (email, URL, IP, file path) from text using regex."""
    patterns = {
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "url": r"https?://[^\s\"']+|ftp://[^\s\"']+",
        "ip": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
        "path": r"/(?:[a-zA-Z0-9._-]+/)*[a-zA-Z0-9._-]+",
        "uuid": r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        "hash": r"\b[0-9a-f]{32,64}\b",
        "domain": r"\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b",
    }
    selected = entity_types.split(",")
    results = {}
    for et in selected:
        et = et.strip()
        pat = patterns.get(et)
        if not pat:
            continue
        matches = re.findall(pat, text, re.IGNORECASE)
        if matches:
            results[et] = list(set(matches))
    if not results:
        return "No entities found."
    entry_id = len(_knowledge_store["entities"])
    _knowledge_store["entities"].append({"id": entry_id, "entities": results})
    out = f"=== Extracted Entities (entry #{entry_id}) ===\n"
    for etype, items in results.items():
        out += f"\n{etype} ({len(items)}):\n"
        for item in items[:20]:
            out += f"  - {item}\n"
        if len(items) > 20:
            out += f"  ... and {len(items) - 20} more\n"
    return out


@tool()
def build_knowledge_graph(entity_ids: str = "") -> str:
    """Build a knowledge graph from extracted entities (simple dict-based adjacency)."""
    ids = [int(x.strip()) for x in entity_ids.split(",") if x.strip().isdigit()] if entity_ids else []
    entries = _knowledge_store["entities"]
    if ids:
        entries = [e for e in entries if e["id"] in ids]
    if not entries:
        return "No entities to build graph from."
    graph = {"nodes": set(), "edges": []}
    for entry in entries:
        for etype, items in entry["entities"].items():
            for item in items:
                graph["nodes"].add(item)
                graph["edges"].append({"type": etype, "value": item})
    entry_id = len(_knowledge_store["graphs"])
    _knowledge_store["graphs"].append({"id": entry_id, "graph": {
        "nodes": list(graph["nodes"]),
        "edges": graph["edges"],
    }})
    out = f"=== Knowledge Graph (entry #{entry_id}) ===\n"
    out += f"Nodes: {len(graph['nodes'])}, Edges: {len(graph['edges'])}\n"
    for edge in graph["edges"][:30]:
        out += f"  [{edge['type']}] {edge['value'][:80]}\n"
    if len(graph["edges"]) > 30:
        out += f"  ... and {len(graph['edges']) - 30} more edges\n"
    return out


@tool()
def query_graph(query: str) -> str:
    """Query the knowledge graph by entity type or value substring."""
    graphs = _knowledge_store.get("graphs", [])
    if not graphs:
        return "No graphs built yet. Use build_knowledge_graph first."
    q = query.lower()
    results = []
    for g in graphs:
        for edge in g["graph"]["edges"]:
            if q in edge["type"].lower() or q in edge["value"].lower():
                results.append(edge)
    if not results:
        return f"No matches for '{query}' in graph."
    out = f"=== Query: '{query}' ({len(results)} results) ===\n"
    for r in results[:50]:
        out += f"  [{r['type']}] {r['value'][:100]}\n"
    if len(results) > 50:
        out += f"  ... and {len(results) - 50} more\n"
    return out
