"""
🕸️ MEMORY GRAPH NETWORK
Knowledge graph of your project - understands semantic relationships between files,
decisions, and past work. Ask "what breaks if I change X?" → get full dependency chain.
Kills: Architecture decision documentation, Dependency analysis tools

Author: OmniClaw Advanced Features
"""

import os
import ast
import json
import hashlib
import sqlite3
from dataclasses import dataclass, field
from typing import Optional, Callable
from datetime import datetime
from enum import Enum
from pathlib import Path


class NodeType(Enum):
    FILE = "file"
    FUNCTION = "function"
    CLASS = "class"
    VARIABLE = "variable"
    DECISION = "decision"
    REQUIREMENT = "requirement"
    BUG = "bug"
    PERSON = "person"


class RelationType(Enum):
    IMPORTS = "imports"
    CALLS = "calls"
    INHERITS = "inherits"
    CONTAINS = "contains"
    DEPENDS_ON = "depends_on"
    RELATED_TO = "related_to"
    CAUSED = "caused"
    FIXED = "fixed"
    AUTHORED = "authored"
    BLOCKED_BY = "blocked_by"


@dataclass
class GraphNode:
    """A node in the knowledge graph"""
    id: str
    type: NodeType
    name: str
    content: str  # Code, decision text, etc.
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def fingerprint(self) -> str:
        return hashlib.md5(f"{self.type.value}:{self.name}".encode()).hexdigest()[:12]


@dataclass
class GraphRelation:
    """A relationship between nodes"""
    source_id: str
    target_id: str
    relation_type: RelationType
    metadata: dict = field(default_factory=dict)
    weight: float = 1.0  # Strength of relationship


class MemoryGraphNetwork:
    """
    Builds and queries a semantic knowledge graph of your project.
    Understands how files, functions, decisions, and bugs relate.
    """
    
    def __init__(self, db_path: str = "./memory_graph.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._init_database()
        
        # Cache for performance
        self._node_cache: dict[str, GraphNode] = {}
        
        # Project root
        self.project_root = "."
    
    def _init_database(self):
        """Initialize graph database schema"""
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS nodes (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                name TEXT NOT NULL,
                content TEXT,
                file_path TEXT,
                line_number INTEGER,
                metadata TEXT,
                created_at TEXT
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS relations (
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                relation_type TEXT NOT NULL,
                metadata TEXT,
                weight REAL DEFAULT 1.0,
                PRIMARY KEY (source_id, target_id, relation_type),
                FOREIGN KEY (source_id) REFERENCES nodes(id),
                FOREIGN KEY (target_id) REFERENCES nodes(id)
            )
        """)
        
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(type)
        """)
        
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_relations_source ON relations(source_id)
        """)
        
        self.conn.commit()
    
    def index_project(self, project_path: str, extensions: list[str] = None):
        """
        Index an entire project into the knowledge graph.
        
        Args:
            project_path: Root directory of project
            extensions: File extensions to index (e.g., ['.py', '.js'])
        """
        self.project_root = project_path
        extensions = extensions or ['.py', '.js', '.ts', '.tsx', '.go', '.java']
        
        for root, dirs, files in os.walk(project_path):
            # Skip common non-code directories
            dirs[:] = [d for d in dirs if d not in [
                'node_modules', '__pycache__', '.git', 'venv', '.venv', 'dist', 'build'
            ]]
            
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, file)
                    self._index_file(file_path)
    
    def _index_file(self, file_path: str):
        """Index a single file"""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            return
        
        rel_path = os.path.relpath(file_path, self.project_root)
        
        # Create file node
        file_node = GraphNode(
            id=self._generate_id(NodeType.FILE, rel_path),
            type=NodeType.FILE,
            name=rel_path,
            content=content[:5000],  # Limit content
            file_path=rel_path,
            metadata={"extension": os.path.splitext(file_path)[1]}
        )
        self._upsert_node(file_node)
        
        # Parse and index code elements
        if file_path.endswith('.py'):
            self._index_python(content, rel_path)
        elif file_path.endswith(('.js', '.ts', '.tsx')):
            self._index_javascript(content, rel_path)
        
        # Index imports/dependencies
        self._index_dependencies(content, rel_path, file_path)
    
    def _index_python(self, content: str, file_path: str):
        """Index Python code elements"""
        
        try:
            tree = ast.parse(content)
        except:
            return
        
        file_id = self._generate_id(NodeType.FILE, file_path)
        
        for node in ast.walk(tree):
            # Classes
            if isinstance(node, ast.ClassDef):
                class_node = GraphNode(
                    id=self._generate_id(NodeType.CLASS, f"{file_path}:{node.name}"),
                    type=NodeType.CLASS,
                    name=node.name,
                    content=ast.get_source_segment(content, node) or "",
                    file_path=file_path,
                    line_number=node.lineno,
                    metadata={"bases": [b.attr if hasattr(b, 'attr') else str(b) for b in node.bases]}
                )
                self._upsert_node(class_node)
                self._add_relation(file_id, class_node.id, RelationType.CONTAINS)
                self._add_relation(class_node.id, file_id, RelationType.CONTAINED_BY)
                
                # Inheritance
                for base in node.bases:
                    base_name = base.attr if hasattr(base, 'attr') else str(base)
                    if base_name:
                        base_id = self._generate_id(NodeType.CLASS, f"{file_path}:{base_name}")
                        self._add_relation(class_node.id, base_id, RelationType.INHERITS)
            
            # Functions
            elif isinstance(node, ast.FunctionDef):
                func_node = GraphNode(
                    id=self._generate_id(NodeType.FUNCTION, f"{file_path}:{node.name}"),
                    type=NodeType.FUNCTION,
                    name=node.name,
                    content=ast.get_source_segment(content, node) or "",
                    file_path=file_path,
                    line_number=node.lineno,
                    metadata={
                        "args": [arg.arg for arg in node.args.args],
                        "is_async": isinstance(node, ast.AsyncFunctionDef)
                    }
                )
                self._upsert_node(func_node)
                self._add_relation(file_id, func_node.id, RelationType.CONTAINS)
                
                # Track function calls within
                for inner in ast.walk(node):
                    if isinstance(inner, ast.Call):
                        if hasattr(inner.func, 'attr'):
                            # Method call
                            pass
                        elif hasattr(inner.func, 'id'):
                            call_id = self._generate_id(
                                NodeType.FUNCTION, 
                                f"{file_path}:{inner.func.id}"
                            )
                            self._add_relation(func_node.id, call_id, RelationType.CALLS)
    
    def _index_javascript(self, content: str, file_path: str):
        """Index JavaScript/TypeScript code elements"""
        
        file_id = self._generate_id(NodeType.FILE, file_path)
        
        # Simple regex-based parsing for JavaScript
        import re
        
        # Functions
        func_pattern = r'(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s*)?\(|(\w+)\s*:\s*(?:async\s*)?\()'
        for match in re.finditer(func_pattern, content):
            func_name = match.group(1) or match.group(2) or match.group(3)
            if func_name and not func_name.startswith('_'):
                func_node = GraphNode(
                    id=self._generate_id(NodeType.FUNCTION, f"{file_path}:{func_name}"),
                    type=NodeType.FUNCTION,
                    name=func_name,
                    file_path=file_path,
                    line_number=content[:match.start()].count('\n') + 1
                )
                self._upsert_node(func_node)
                self._add_relation(file_id, func_node.id, RelationType.CONTAINS)
        
        # Classes
        class_pattern = r'class\s+(\w+)'
        for match in re.finditer(class_pattern, content):
            class_name = match.group(1)
            class_node = GraphNode(
                id=self._generate_id(NodeType.CLASS, f"{file_path}:{class_name}"),
                type=NodeType.CLASS,
                name=class_name,
                file_path=file_path,
                line_number=content[:match.start()].count('\n') + 1
            )
            self._upsert_node(class_node)
            self._add_relation(file_id, class_node.id, RelationType.CONTAINS)
    
    def _index_dependencies(self, content: str, file_path: str, full_path: str):
        """Index import/require statements"""
        
        file_id = self._generate_id(NodeType.FILE, file_path)
        
        if file_path.endswith('.py'):
            # Python imports
            import re
            pattern = r'^(?:from\s+(\S+)|import\s+(\S+))'
            for match in re.finditer(pattern, content, re.MULTILINE):
                module = match.group(1) or match.group(2)
                if module and not module.startswith('.'):
                    # Create module node
                    module_id = self._generate_id(NodeType.FILE, module)
                    self._add_relation(file_id, module_id, RelationType.IMPORTS)
        
        elif file_path.endswith(('.js', '.ts')):
            # JavaScript imports
            import re
            pattern = r'(?:import\s+.*?\s+from\s+[\'"](.+?)[\'"]|require\([\'"](.+?)[\'"]\))'
            for match in re.finditer(pattern, content):
                module = match.group(1) or match.group(2)
                if module:
                    module_id = self._generate_id(NodeType.FILE, module)
                    self._add_relation(file_id, module_id, RelationType.IMPORTS)
    
    def _generate_id(self, node_type: NodeType, name: str) -> str:
        """Generate unique ID for a node"""
        return f"{node_type.value}:{name}"
    
    def _upsert_node(self, node: GraphNode):
        """Insert or update a node"""
        
        self.conn.execute("""
            INSERT OR REPLACE INTO nodes (id, type, name, content, file_path, line_number, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            node.id, node.type.value, node.name, node.content,
            node.file_path, node.line_number,
            json.dumps(node.metadata), node.created_at.isoformat()
        ))
        self.conn.commit()
        
        self._node_cache[node.id] = node
    
    def _add_relation(
        self, 
        source_id: str, 
        target_id: str, 
        relation_type: RelationType,
        weight: float = 1.0
    ):
        """Add a relationship between nodes"""
        
        self.conn.execute("""
            INSERT OR REPLACE INTO relations (source_id, target_id, relation_type, weight)
            VALUES (?, ?, ?, ?)
        """, (source_id, target_id, relation_type.value, weight))
        self.conn.commit()
    
    def add_decision(self, title: str, content: str, related_files: list[str] = None):
        """Add an architectural decision to the graph"""
        
        decision_node = GraphNode(
            id=self._generate_id(NodeType.DECISION, title),
            type=NodeType.DECISION,
            name=title,
            content=content,
            metadata={"date": datetime.now().isoformat()}
        )
        self._upsert_node(decision_node)
        
        if related_files:
            for file_path in related_files:
                file_id = self._generate_id(NodeType.FILE, file_path)
                # Check if file exists in graph
                cursor = self.conn.execute("SELECT id FROM nodes WHERE id = ?", (file_id,))
                if cursor.fetchone():
                    self._add_relation(decision_node.id, file_id, RelationType.RELATED_TO)
        
        return decision_node
    
    def query_impact(
        self, 
        file_or_function: str,
        depth: int = 3
    ) -> dict:
        """
        Query what breaks if you change something.
        
        Args:
            file_or_function: File path or function name
            depth: How deep to traverse the dependency graph
        
        Returns:
            Impact analysis with affected components
        """
        
        # Find the node
        node_id = None
        for ntype in [NodeType.FILE, NodeType.FUNCTION, NodeType.CLASS]:
            potential_id = self._generate_id(ntype, file_or_function)
            cursor = self.conn.execute("SELECT id FROM nodes WHERE id = ?", (potential_id,))
            if cursor.fetchone():
                node_id = potential_id
                break
        
        if not node_id:
            return {"error": f"Node not found: {file_or_function}"}
        
        # BFS to find all dependent nodes
        affected = self._bfs_impact(node_id, depth)
        
        # Categorize by type
        by_type = {}
        for node_id in affected:
            node = self._get_node(node_id)
            if node:
                ntype = node.type.value
                if ntype not in by_type:
                    by_type[ntype] = []
                by_type[ntype].append({
                    "name": node.name,
                    "file": node.file_path,
                    "line": node.line_number
                })
        
        return {
            "target": file_or_function,
            "total_affected": len(affected),
            "by_type": by_type,
            "risk_level": self._calculate_risk(affected),
            "recommendation": self._generate_recommendation(affected)
        }
    
    def _bfs_impact(self, start_id: str, depth: int) -> set:
        """Breadth-first search to find all affected nodes"""
        
        visited = set()
        queue = [(start_id, 0)]
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited:
                continue
            visited.add(current_id)
            
            if current_depth >= depth:
                continue
            
            # Find relations where current node is source
            cursor = self.conn.execute("""
                SELECT target_id, relation_type FROM relations 
                WHERE source_id = ?
            """, (current_id,))
            
            for row in cursor:
                target_id, rel_type = row
                
                # Skip certain relation types
                if rel_type in ['imports', 'calls']:
                    weight = 1.0
                else:
                    weight = 0.5
                
                if weight >= 0.3:  # Only follow strong relations
                    queue.append((target_id, current_depth + 1))
        
        visited.discard(start_id)
        return visited
    
    def _get_node(self, node_id: str) -> Optional[GraphNode]:
        """Get node by ID"""
        
        if node_id in self._node_cache:
            return self._node_cache[node_id]
        
        cursor = self.conn.execute("""
            SELECT id, type, name, content, file_path, line_number, metadata, created_at
            FROM nodes WHERE id = ?
        """, (node_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        node = GraphNode(
            id=row[0],
            type=NodeType(row[1]),
            name=row[2],
            content=row[3] or "",
            file_path=row[4],
            line_number=row[5],
            metadata=json.loads(row[6] or "{}"),
            created_at=datetime.fromisoformat(row[7])
        )
        
        self._node_cache[node_id] = node
        return node
    
    def _calculate_risk(self, affected_nodes: set) -> str:
        """Calculate risk level based on affected components"""
        
        high_risk_types = {NodeType.FILE.value, NodeType.CLASS.value}
        
        high_risk_count = sum(
            1 for nid in affected_nodes 
            if self._get_node(nid) and self._get_node(nid).type in [
                NodeType.FILE, NodeType.CLASS
            ]
        )
        
        if high_risk_count > 10:
            return "HIGH"
        elif high_risk_count > 5:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _generate_recommendation(self, affected_nodes: set) -> str:
        """Generate recommendation for changes"""
        
        count = len(affected_nodes)
        
        if count == 0:
            return "Safe to change - no dependencies found"
        elif count < 5:
            return f"Low risk - {count} components affected. Test these components."
        elif count < 15:
            return f"Medium risk - {count} components affected. Run integration tests."
        else:
            return f"HIGH RISK - {count} components affected. Full regression testing required."
    
    def find_related_decisions(self, file_path: str) -> list[dict]:
        """Find architectural decisions related to a file"""
        
        file_id = self._generate_id(NodeType.FILE, file_path)
        
        cursor = self.conn.execute("""
            SELECT DISTINCT n.id, n.name, n.content, n.metadata
            FROM nodes n
            JOIN relations r ON (r.source_id = n.id OR r.target_id = n.id)
            WHERE (r.source_id = ? OR r.target_id = ?)
            AND n.type = ?
        """, (file_id, file_id, NodeType.DECISION.value))
        
        results = []
        for row in cursor:
            results.append({
                "title": row[1],
                "content": row[2],
                "metadata": json.loads(row[3] or "{}")
            })
        
        return results
    
    def export_graph(self, format: str = "json") -> str:
        """Export the knowledge graph"""
        
        nodes = []
        cursor = self.conn.execute("SELECT * FROM nodes")
        for row in cursor:
            nodes.append({
                "id": row[0],
                "type": row[1],
                "name": row[2],
                "content": row[3],
                "file_path": row[4]
            })
        
        relations = []
        cursor = self.conn.execute("SELECT * FROM relations")
        for row in cursor:
            relations.append({
                "source": row[0],
                "target": row[1],
                "type": row[2],
                "weight": row[4]
            })
        
        return json.dumps({
            "nodes": nodes,
            "relations": relations
        }, indent=2)


# Demo
if __name__ == "__main__":
    print("🕸️ MEMORY GRAPH NETWORK")
    print("=" * 50)
    print("""
Usage:
    
    from omniclaw_advanced_features import MemoryGraphNetwork
    
    # Initialize
    graph = MemoryGraphNetwork("./my_project_graph.db")
    
    # Index your project
    graph.index_project("/path/to/your/project", extensions=['.py'])
    
    # Add architectural decisions
    graph.add_decision(
        title="Use PostgreSQL for user data",
        content="PostgreSQL chosen for ACID compliance and JSON support",
        related_files=["models/user.py", "db/migrations/001.sql"]
    )
    
    # Query impact - what breaks if I change this?
    impact = graph.query_impact("models/user.py", depth=2)
    print(f"Affects: {impact['total_affected']} components")
    print(f"Risk: {impact['risk_level']}")
    print(f"Recommendation: {impact['recommendation']}")
    
    # Find related decisions
    decisions = graph.find_related_decisions("models/user.py")
    for d in decisions:
        print(f"Decision: {d['title']}")
""")
