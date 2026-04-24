"""
PentAGI Knowledge Synchronizer

Polls the PentAGI API for completed vulnerability discovery flows and 
stores their Markdown artifacts in OmniClaw's TemporalMemoryV2 vector store.
"""

import logging
import asyncio
from typing import List, Dict

try:
    from sys import path as sys_path
    from pathlib import Path
    sys_path.append(str(Path(__file__).resolve().parent.parent.parent))
    from core.temporal_memory_v2 import TemporalMemoryV2
except ImportError:
    TemporalMemoryV2 = None

from .client import PentagiClient

logger = logging.getLogger(__name__)

async def synchronize_pentagi_reports(memory: TemporalMemoryV2 = None, client: PentagiClient = None):
    """
    Poll PentAGI for completed tasks and pull artifacts into the OmniClaw memory graph.
    """
    if not memory and TemporalMemoryV2:
        memory = TemporalMemoryV2()
    
    if not memory:
        logger.warning("TemporalMemoryV2 not available. Skipping sync.")
        return

    client = client or PentagiClient()
    success = await client.authenticate()
    if not success:
        return
        
    # Fetch completed flows (hypothetical query based on generic schemas)
    query = """
    query GetCompletedFlows {
        flows(status: "completed", limit: 10) {
            id
            target
            artifacts {
                type
                content
            }
        }
    }
    """
    try:
        data = await client.run_graphql_query(query)
        flows = data.get("data", {}).get("flows", [])
        
        synced_count = 0
        for flow in flows:
            flow_id = flow.get("id")
            target = flow.get("target", "unknown")
            artifacts = flow.get("artifacts", [])
            
            # Combine Markdown artifacts
            report_content = ""
            for art in artifacts:
                if art.get("type") in ["report", "markdown"]:
                    report_content += f"\n{art.get('content')}"
            
            if report_content:
                memory_text = f"PentAGI Autonomous Pentest Report for {target} (Flow {flow_id}):\n{report_content}"
                # In a real impl, you'd check if it's already embedded.
                memory.add_experience(memory_text, importance=0.9)
                synced_count += 1
                
        if synced_count > 0:
            logger.info(f"Synchronized {synced_count} PentAGI reports into OmniClaw Temporal Memory.")
            
    except Exception as e:
        logger.error(f"Failed to synchronize PentAGI reports: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(synchronize_pentagi_reports())
