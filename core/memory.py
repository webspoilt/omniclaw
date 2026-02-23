#!/usr/bin/env python3
"""
OmniClaw Vector Memory System
Persistent memory using vector database for context retention
"""

import json
import logging
from typing import Dict, List, Optional, Any
import numpy as np
import time
import hashlib
from pathlib import Path

logger = logging.getLogger("OmniClaw.Memory")


class VectorMemory:
    """
    Vector-based memory system for persistent context storage
    Uses FAISS or similar for vector search
    """
    
    def __init__(self, db_path: str = "./memory_db", embedding_provider: str = "openai"):
        self.db_path = Path(db_path)
        self.db_path.mkdir(parents=True, exist_ok=True)
        self.embedding_provider = embedding_provider
        
        # Initialize embedding function
        self.embedder = self._initialize_embedder()
        
        # Memory stores
        self.conversations: Dict[str, List[Dict]] = {}
        self.tasks: Dict[str, Dict] = {}
        self.knowledge: Dict[str, Dict] = {}
        self.embeddings: Dict[str, np.ndarray] = {}
        
        # Try to load FAISS
        self.faiss_available = False
        self.index = None
        self._initialize_vector_db()
        
        # Load existing data
        self._load_memory()
        
        logger.info(f"VectorMemory initialized at {db_path}")
    
    def _initialize_embedder(self):
        """Initialize the embedding function"""
        if self.embedding_provider == "openai":
            try:
                from openai import OpenAI
                client = OpenAI()
                
                def embed(text: str) -> List[float]:
                    response = client.embeddings.create(
                        model="text-embedding-ada-002",
                        input=text
                    )
                    return response.data[0].embedding
                
                return embed
            except Exception as e:
                logger.warning(f"OpenAI embedding failed: {e}, using fallback")
                return self._fallback_embedder()
        
        elif self.embedding_provider == "ollama":
            def ollama_embed(text: str) -> List[float]:
                import requests
                response = requests.post(
                    "http://localhost:11434/api/embeddings",
                    json={"model": "nomic-embed-text", "prompt": text}
                )
                return response.json()["embedding"]
            return ollama_embed
        
        else:
            return self._fallback_embedder()
    
    def _fallback_embedder(self):
        """Simple fallback embedding using hashing"""
        def embed(text: str, dim: int = 384) -> List[float]:
            # Simple hash-based embedding
            hash_val = hashlib.md5(text.encode()).hexdigest()
            np.random.seed(int(hash_val, 16) % (2**32))
            return np.random.randn(dim).tolist()
        return embed
    
    def _initialize_vector_db(self):
        """Initialize vector database (FAISS)"""
        try:
            import faiss
            self.faiss_available = True
            
            # Determine embedding dimension
            sample_embedding = self.embedder("sample text")
            dim = len(sample_embedding)
            
            # Create index
            self.index = faiss.IndexFlatL2(dim)
            self.embedding_map: List[str] = []  # Maps index to memory key
            
            logger.info(f"FAISS initialized with dimension {dim}")
        except ImportError:
            logger.warning("FAISS not available, using in-memory search")
            self.faiss_available = False
    
    def _load_memory(self):
        """Load existing memory from disk"""
        conversations_path = self.db_path / "conversations.json"
        tasks_path = self.db_path / "tasks.json"
        knowledge_path = self.db_path / "knowledge.json"
        
        if conversations_path.exists():
            with open(conversations_path) as f:
                self.conversations = json.load(f)
        
        if tasks_path.exists():
            with open(tasks_path) as f:
                self.tasks = json.load(f)
        
        if knowledge_path.exists():
            with open(knowledge_path) as f:
                self.knowledge = json.load(f)
        
        logger.info(f"Loaded {len(self.conversations)} conversations, {len(self.tasks)} tasks, {len(self.knowledge)} knowledge items")
    
    def _save_memory(self):
        """Save memory to disk"""
        with open(self.db_path / "conversations.json", 'w') as f:
            json.dump(self.conversations, f, indent=2)
        
        with open(self.db_path / "tasks.json", 'w') as f:
            json.dump(self.tasks, f, indent=2)
        
        with open(self.db_path / "knowledge.json", 'w') as f:
            json.dump(self.knowledge, f, indent=2)
    
    async def store(self, key: str, value: Any, memory_type: str = "knowledge"):
        """
        Store a memory item
        
        Args:
            key: Unique identifier
            value: Data to store
            memory_type: Type of memory (knowledge, conversation, task)
        """
        timestamp = time.time()
        
        memory_item = {
            "key": key,
            "value": value,
            "type": memory_type,
            "timestamp": timestamp,
            "access_count": 0,
            "last_accessed": timestamp
        }
        
        # Store in appropriate collection
        if memory_type == "conversation":
            if key not in self.conversations:
                self.conversations[key] = []
            self.conversations[key].append(memory_item)
        elif memory_type == "task":
            self.tasks[key] = memory_item
        else:
            self.knowledge[key] = memory_item
        
        # Create and store embedding
        text_to_embed = self._extract_text(value)
        embedding = self.embedder(text_to_embed)
        self.embeddings[key] = np.array(embedding)
        
        # Add to FAISS index
        if self.faiss_available and self.index is not None:
            self.index.add(np.array([embedding]).astype('float32'))
            self.embedding_map.append(key)
        
        # Save to disk
        self._save_memory()
        
        logger.debug(f"Stored memory: {key}")
    
    async def store_task(self, task):
        """Store a task in memory"""
        task_dict = {
            "id": task.id,
            "goal": task.goal,
            "subtasks": [
                {
                    "id": st.id,
                    "description": st.description,
                    "role": st.role.value,
                    "status": st.status.value,
                    "result": st.result
                }
                for st in task.subtasks
            ],
            "final_result": task.final_result,
            "created_at": task.created_at,
            "completed_at": task.completed_at
        }
        
        await self.store(task.id, task_dict, "task")
    
    async def search(self, query: str, limit: int = 5, memory_type: Optional[str] = None) -> List[Dict]:
        """
        Search memory using semantic similarity
        
        Args:
            query: Search query
            limit: Maximum results
            memory_type: Filter by memory type
            
        Returns:
            List of matching memory items
        """
        query_embedding = np.array(self.embedder(query))
        
        # Search based on available methods
        if self.faiss_available and self.index is not None and len(self.embedding_map) > 0:
            results = self._faiss_search(query_embedding, limit)
        else:
            results = self._brute_force_search(query_embedding, limit)
        
        # Filter by type if specified
        if memory_type:
            results = [r for r in results if r.get("type") == memory_type]
        
        # Update access stats
        for result in results:
            key = result.get("key")
            if key in self.knowledge:
                self.knowledge[key]["access_count"] += 1
                self.knowledge[key]["last_accessed"] = time.time()
        
        return results[:limit]
    
    def _faiss_search(self, query_embedding: np.ndarray, limit: int) -> List[Dict]:
        """Search using FAISS"""
        D, I = self.index.search(query_embedding.reshape(1, -1).astype('float32'), limit)
        
        results = []
        for idx, distance in zip(I[0], D[0]):
            if idx < len(self.embedding_map):
                key = self.embedding_map[idx]
                memory_item = self._get_memory_item(key)
                if memory_item:
                    memory_item["similarity_score"] = float(1 / (1 + distance))
                    results.append(memory_item)
        
        return results
    
    def _brute_force_search(self, query_embedding: np.ndarray, limit: int) -> List[Dict]:
        """Brute force similarity search"""
        similarities = []
        
        for key, embedding in self.embeddings.items():
            similarity = np.dot(query_embedding, embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(embedding)
            )
            similarities.append((key, similarity))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for key, similarity in similarities[:limit]:
            memory_item = self._get_memory_item(key)
            if memory_item:
                memory_item["similarity_score"] = float(similarity)
                results.append(memory_item)
        
        return results
    
    def _get_memory_item(self, key: str) -> Optional[Dict]:
        """Get a memory item by key"""
        if key in self.knowledge:
            return self.knowledge[key]
        if key in self.tasks:
            return self.tasks[key]
        for conv_list in self.conversations.values():
            for item in conv_list:
                if item["key"] == key:
                    return item
        return None
    
    def _extract_text(self, value: Any) -> str:
        """Extract searchable text from value"""
        if isinstance(value, str):
            return value
        elif isinstance(value, dict):
            return json.dumps(value)
        elif isinstance(value, list):
            return " ".join(str(item) for item in value)
        else:
            return str(value)
    
    async def find_similar_decompositions(self, goal: str) -> Optional[Dict]:
        """Find similar goal decompositions"""
        results = await self.search(goal, limit=3, memory_type="task")
        
        if results:
            # Return the most similar task's decomposition
            best_match = results[0]
            return best_match.get("value", {})
        
        return None
    
    async def get_conversation_history(self, conversation_id: str, limit: int = 10) -> List[Dict]:
        """Get conversation history"""
        if conversation_id in self.conversations:
            history = self.conversations[conversation_id]
            return sorted(history, key=lambda x: x["timestamp"], reverse=True)[:limit]
        return []
    
    async def add_to_conversation(self, conversation_id: str, message: Dict):
        """Add a message to conversation history"""
        await self.store(
            f"{conversation_id}_{time.time()}",
            message,
            "conversation"
        )
        
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
        
        self.conversations[conversation_id].append({
            **message,
            "timestamp": time.time()
        })
        
        self._save_memory()
    
    async def get_context(self, query: str, conversation_id: Optional[str] = None, limit: int = 5) -> Dict[str, Any]:
        """
        Get relevant context for a query
        
        Args:
            query: The query to get context for
            conversation_id: Optional conversation ID for recent history
            limit: Maximum items to retrieve
            
        Returns:
            Context dictionary
        """
        context = {
            "relevant_memories": [],
            "conversation_history": [],
            "related_tasks": []
        }
        
        # Search for relevant memories
        memories = await self.search(query, limit=limit)
        context["relevant_memories"] = memories
        
        # Get conversation history
        if conversation_id:
            context["conversation_history"] = await self.get_conversation_history(conversation_id, limit=5)
        
        # Get related tasks
        tasks = await self.search(query, limit=3, memory_type="task")
        context["related_tasks"] = tasks
        
        return context
    
    def clear_memory(self, memory_type: Optional[str] = None):
        """Clear memory (optionally by type)"""
        if memory_type == "conversation":
            self.conversations = {}
        elif memory_type == "task":
            self.tasks = {}
        elif memory_type == "knowledge":
            self.knowledge = {}
        else:
            self.conversations = {}
            self.tasks = {}
            self.knowledge = {}
            self.embeddings = {}
            if self.faiss_available:
                self._initialize_vector_db()
        
        self._save_memory()
        logger.info(f"Cleared memory (type: {memory_type})")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        return {
            "conversations": len(self.conversations),
            "tasks": len(self.tasks),
            "knowledge_items": len(self.knowledge),
            "total_embeddings": len(self.embeddings),
            "faiss_enabled": self.faiss_available,
            "db_path": str(self.db_path)
        }
