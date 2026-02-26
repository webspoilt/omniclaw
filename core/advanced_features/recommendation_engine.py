import logging
import litellm

logger = logging.getLogger("OmniClaw.RecommendationEngine")

try:
    import chromadb
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logger.warning("chromadb not installed. Recommendation Engine degraded.")

class OmniClawState:
    """
    DIEN-style Interest Evolution Tracker.
    Tracks recent actions to predict the current "Mode" of the user.
    """
    def __init__(self, history_size=5):
        self.interest_evolution = []
        self.history_size = history_size

    def update_state(self, action: str):
        self.interest_evolution.append(action)
        if len(self.interest_evolution) > self.history_size:
            self.interest_evolution.pop(0)

    def predict_mode(self) -> str:
        security_keywords = ['scan', 'hack', 'audit', 'threat', 'vulnerability', 'nmap', 'exploit']
        creative_keywords = ['design', 'write', 'draw', 'generate', 'create', 'blog']
        
        recent = " ".join(self.interest_evolution[-3:]).lower()
        
        if any(word in recent for word in security_keywords):
            return "GHOST_MODE (Aggressive Security)"
        if any(word in recent for word in creative_keywords):
            return "CREATIVE_MODE (Brainstorm & Design)"
            
        return "DEV_MODE (Standard Development)"

class RecommendationEngine:
    """
    3-Layer Recommendation Engine for Tool Selection:
    1. Candidate Generation (ChromaDB / Vector Search)
    2. Deep Interest Ranking (DIN / LLM Attention)
    3. Interest Evolution (DIEN / State Tracker)
    """
    def __init__(self, embed_model="ollama/mxbai-embed-large", llm_model="ollama/llama3"):
        self.embed_model = embed_model
        self.llm_model = llm_model
        self.state = OmniClawState()
        
        self.collection = None
        if CHROMA_AVAILABLE:
            try:
                self.client = chromadb.Client()
                self.collection = self.client.create_collection(name="omniclaw_tools_v2")
                self._seed_tools()
            except Exception as e:
                logger.error(f"Failed to initialize ChromaDB for Recommendations: {e}")

    def _seed_tools(self):
        """Seed initial tools into the vector database"""
        tools = [
            {"id": "t1", "desc": "web_search - Search the internet for real-time information"},
            {"id": "t2", "desc": "shell_execute - Run terminal commands, system administration"},
            {"id": "t3", "desc": "file_operation - Read/write local files and manage codebase"},
            {"id": "t4", "desc": "browser_control - Automate web browser to scrape or fill forms"},
            {"id": "t5", "desc": "kernel_alerts - Read shadow kernel eBPF anomalies"},
            {"id": "t6", "desc": "quantum_script - Execute QASM on quantum hardware"}
        ]
        
        try:
            for t in tools:
                # Using litellm for embeddings to keep it model-agnostic
                response = litellm.embedding(model=self.embed_model, input=[t['desc']])
                self.collection.add(
                    ids=[t['id']],
                    embeddings=[response.data[0]['embedding']],
                    documents=[t['desc']]
                )
        except Exception as e:
            logger.warning(f"Could not seed tools (is Ollama {self.embed_model} running?): {e}")

    def get_candidates(self, user_query: str, n=3) -> list:
        """1. Candidate Generation via Vector Search"""
        if not self.collection:
            return ["All local tools (Vector DB unavailable)"]
            
        try:
            query_emb = litellm.embedding(model=self.embed_model, input=[user_query]).data[0]['embedding']
            results = self.collection.query(query_embeddings=[query_emb], n_results=n)
            return results['documents'][0]
        except Exception as e:
            logger.error(f"Candidate generation failed: {e}")
            return ["Fallback: web_search, file_operation, shell_execute"]

    async def rank_actions(self, query: str, candidates: list) -> str:
        """2. Deep Interest (DIN Style) Ranking via LLM Attention"""
        history = self.state.interest_evolution
        mode = self.state.predict_mode()
        
        prompt = f"""
        User Task: {query}
        Current Agent Mode: {mode}
        Session History (Recent Actions): {history[-3:] if history else 'None'}
        Candidate Tools: {candidates}
        
        Based on the user's intent and history, pick the SINGLE BEST tool from the candidates to use next.
        Return only the tool name.
        """
        
        try:
            response = await litellm.acompletion(
                model=self.llm_model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Action ranking failed: {e}")
            if candidates:
                return candidates[0]
            return "unknown"

# Singleton instance
recommendation_engine = RecommendationEngine()
