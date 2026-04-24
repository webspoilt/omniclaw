"""
OmniClaw Stealth Scraper (Powered by Scrapling)

Provides extreme anti-bot bypass capabilities (Cloudflare Turnstile, Kasada, etc.)
for the OmniClaw Scout agent to read protected targets.
"""

import logging
from typing import Dict, Any

try:
    from scrapling.fetchers import StealthyFetcher
    SCRAPLING_AVAILABLE = True
except ImportError:
    SCRAPLING_AVAILABLE = False

logger = logging.getLogger(__name__)

class StealthScraper:
    def __init__(self):
        if not SCRAPLING_AVAILABLE:
            logger.warning("Scrapling is not installed. Please run `pip install scrapling[all]`.")

    def scrape(self, url: str, css_selector: str = "body", solve_cloudflare: bool = True) -> Dict[str, Any]:
        """
        Perform a stealth fetch on the URL and return adaptive CSS selection content.
        Uses Scrapling to bypass protections and impersonate real browsers.
        """
        if not SCRAPLING_AVAILABLE:
            return {"status": "error", "error": "Scrapling library not installed."}

        logger.info(f"Stealth scraping {url} using selector '{css_selector}'...")
        try:
            # We use an isolated request (headless active)
            # adaptive=True allows for finding slightly changed classes when crawling
            page = StealthyFetcher.fetch(url, headless=True, solve_cloudflare=solve_cloudflare)
            results = page.css(css_selector, adaptive=True).getall()
            
            # Additional cleanup
            if results:
                content = "\n".join([str(res) for res in results])
                return {
                    "status": "success",
                    "url": url,
                    "length": len(content),
                    "content": content
                }
            else:
                return {
                    "status": "warning",
                    "url": url,
                    "message": "Selector did not match any content."
                }

        except Exception as e:
            logger.error(f"Stealth scraping failed for {url}: {e}")
            return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    scraper = StealthScraper()
    print("Stealth Scraper Initialized.")
