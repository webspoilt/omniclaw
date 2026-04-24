import aiohttp
import logging
from typing import List, Dict, Any
from core.skills.registry import tool

logger = logging.getLogger(__name__)

class SocialThreatSpider:
    """
    Crawl security-centric social feeds and forums for real-time threat intelligence.
    Inspired by BettaFish's MindSpider.
    """

    SOURCES = {
        "github": "https://api.github.com/search/repositories?q={query}+sort:updated",
        "reddit_sec": "https://www.reddit.com/r/netsec/search.json?q={query}&restrict_sr=1",
        "hacker_news": "https://hn.algolia.com/api/v1/search?query={query}"
    }

    @tool(needs_confirmation=True)
    async def crawl_threat_intelligence(self, query: str) -> List[Dict[str, Any]]:
        """
        Crawls GitHub, Reddit, and Hacker News for specific security intelligence.
        
        Args:
            query: The keyword or CVE to search for.
            
        Returns:
            A list of intelligence items (Title, URL, Summary).
        """
        logger.info(f"Spidering social feeds for: {query}")
        results = []
        
        async with aiohttp.ClientSession() as session:
            # GitHub Search
            try:
                async with session.get(self.SOURCES["github"].format(query=query)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for item in data.get("items", [])[:5]:
                            results.append({
                                "source": "GitHub",
                                "title": item["name"],
                                "url": item["html_url"],
                                "summary": item["description"]
                            })
            except Exception as e:
                logger.error(f"GitHub spider error: {e}")

            # Hacker News Search
            try:
                async with session.get(self.SOURCES["hacker_news"].format(query=query)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for item in data.get("hits", [])[:5]:
                            results.append({
                                "source": "HackerNews",
                                "title": item["title"],
                                "url": f"https://news.ycombinator.com/item?id={item['objectID']}",
                                "summary": f"Points: {item.get('points', 0)} | Comments: {item.get('num_comments', 0)}"
                            })
            except Exception as e:
                logger.error(f"HN spider error: {e}")

        return results

# Global instance
social_spider = SocialThreatSpider()
