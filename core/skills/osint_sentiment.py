import logging
from typing import Dict, Any, List
from core.skills.registry import tool

logger = logging.getLogger(__name__)

class OSINTSentimentSkill:
    """
    Analyzes public sentiment and chatter regarding specific vulnerabilities, 
    exploits, or security researchers to determine real-world risk levels.
    Inspired by BettaFish's sentiment engine.
    """
    
    def __init__(self):
        # In a real scenario, this might load a local BERT/RoBERTa model
        # or connect to an LLM endpoint.
        pass

    @tool(needs_confirmation=False)
    async def analyze_threat_sentiment(self, query: str, context: List[str]) -> Dict[str, Any]:
        """
        Analyzes the social sentiment of a security-related query based on provided context.
        
        Args:
            query: The security topic (e.g., 'CVE-2024-1234')
            context: A list of text snippets (tweets, forum posts, news) to analyze.
            
        Returns:
            A dictionary containing sentiment scores and risk categorization.
        """
        logger.info(f"Analyzing threat sentiment for: {query}")
        
        # Simulated analysis logic
        scores = {
            "exploitation_noise": 0.0,
            "research_interest": 0.0,
            "patch_availability": 0.0,
            "general_sentiment": "NEUTRAL"
        }
        
        if not context:
            return {"error": "No context provided for analysis", "sentiment": scores}

        # Simplified keyword-based heuristic (representative of a first-pass agent)
        high_risk_keywords = ["poc", "exploit", "rce", "zero-day", "0day", "wild", "bypass"]
        research_keywords = ["analysis", "write-up", "paper", "vulnerability", "disclosure"]
        
        text_blob = " ".join(context).lower()
        
        risk_count = sum(1 for word in high_risk_keywords if word in text_blob)
        research_count = sum(1 for word in research_keywords if word in text_blob)
        
        scores["exploitation_noise"] = min(1.0, risk_count / 5.0)
        scores["research_interest"] = min(1.0, research_count / 5.0)
        
        if scores["exploitation_noise"] > 0.6:
            scores["general_sentiment"] = "CRITICAL_THREAT"
        elif scores["exploitation_noise"] > 0.3:
            scores["general_sentiment"] = "ACTIVE_EXPLOITATION"
        elif scores["research_interest"] > 0.5:
            scores["general_sentiment"] = "RESEARCH_HYPE"
        
        return {
            "topic": query,
            "sentiment_report": scores,
            "summary": f"Detected {scores['general_sentiment']} for {query}. Exploitation noise at {scores['exploitation_noise']*100}%."
        }

# Global instance for registration
osint_sentiment = OSINTSentimentSkill()
