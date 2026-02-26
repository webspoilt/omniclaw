import faiss
import numpy as np
import time
import logging
import threading
from sentence_transformers import SentenceTransformer

logger = logging.getLogger("OmniClaw.TemporalMemoryV2")

try:
    model = SentenceTransformer('all-MiniLM-L6-v2')
except Exception as e:
    logger.warning(f"Could not load SentenceTransformer locally, embeddings will fail if used: {e}")
    model = None

class TemporalMemoryV2:
    """
    Temporal Memory with Entropy-based Decay.
    Stores facts with timestamps and periodically prunes old/low-value memories using a decay score.
    """
    def __init__(self, dim=384, decay_rate=0.01):
        self.dim = dim
        self.index = faiss.IndexFlatL2(dim)
        self.memories = []          # list of (text, timestamp, embedding)
        self.decay_rate = decay_rate
        self.lock = threading.Lock()
        
        # Start decay thread
        self.running = True
        self.decay_thread = threading.Thread(target=self._auto_decay_loop, daemon=True)
        self.decay_thread.start()

    def add(self, text: str):
        if not model:
            logger.error("SentenceTransformer model not loaded. Cannot add to temporal memory.")
            return
            
        try:
            emb = model.encode([text])[0]
            with self.lock:
                self.index.add(np.array([emb], dtype=np.float32))
                self.memories.append((text, time.time(), emb))
            logger.debug(f"Added memory: '{text[:30]}...'")
        except Exception as e:
            logger.error(f"Failed to add memory: {e}")

    def query(self, query: str, top_k=5) -> list:
        if not model:
            return []
            
        with self.lock:
            if not self.memories:
                return []
                
        try:
            q_emb = model.encode([query])[0]
            with self.lock:
                # Need to cap top_k to actual size
                k = min(top_k, len(self.memories))
                if k == 0:
                    return []
                    
                distances, indices = self.index.search(np.array([q_emb], dtype=np.float32), k)
                
                # Filter out -1 indices which FAISS returns if not enough elements
                valid_indices = [i for i in indices[0] if i >= 0]
                return [self.memories[i][0] for i in valid_indices]
        except Exception as e:
            logger.error(f"Failed to query temporal memory: {e}")
            return []

    def decay_and_prune(self, threshold=0.5):
        """
        Calculates the entropy-like score of memories based on age.
        Prunes memories that fall below the given threshold.
        """
        with self.lock:
            if not self.memories:
                return
                
            now = time.time()
            new_memories = []
            new_embs = []
            pruned_count = 0
            
            for text, ts, emb in self.memories:
                age = now - ts
                # score: 1 at t=0, decays to 0 based on decay_rate * age
                score = np.exp(-self.decay_rate * age)   
                
                if score > threshold:
                    new_memories.append((text, ts, emb))
                    new_embs.append(emb)
                else:
                    pruned_count += 1
                    
            if pruned_count > 0:
                logger.info(f"Temporal Memory Pruned {pruned_count} old memories.")
                
                # Rebuild FAISS index
                self.memories = new_memories
                if new_embs:
                    self.index = faiss.IndexFlatL2(self.dim)
                    self.index.add(np.array(new_embs, dtype=np.float32))
                else:
                    self.index = faiss.IndexFlatL2(self.dim)  # empty

    def _auto_decay_loop(self):
        """Background thread to periodically run decay and pruning."""
        while self.running:
            # Run every 60 seconds (or adjust based on decay_rate)
            time.sleep(60)
            try:
                self.decay_and_prune()
            except Exception as e:
                logger.error(f"Temporal Memory decay loop error: {e}")

    def stop(self):
        self.running = False
        if self.decay_thread.is_alive():
            self.decay_thread.join(timeout=1)
