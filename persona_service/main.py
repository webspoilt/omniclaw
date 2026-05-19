import asyncio
import logging
import json
import os
import re
from typing import List, Dict

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("PersonaService")

PLAYWRIGHT_AVAILABLE = False
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
    logger.info("Playwright framework found.")
except ImportError:
    logger.warning("Playwright not installed. Profile scraping will use simulated DOM parser fallback.")

class IdentityStyleAnalyzer:
    """Analyzes text datasets to construct style footprints for identity mirroring."""
    
    @staticmethod
    def analyze(texts: List[str]) -> Dict:
        if not texts:
            return {"avg_length": 0, "punctuation_density": 0, "vocabulary_diversity": 0, "top_tokens": []}
            
        all_words = []
        sentence_lengths = []
        punctuation_count = 0
        total_chars = 0
        
        punctuation_regex = re.compile(r'[.,!?;:]')
        
        for text in texts:
            # Word tokenization
            words = [w.lower() for w in re.findall(r'\b\w+\b', text)]
            all_words.extend(words)
            
            # Sentence counting
            sentences = [s for s in re.split(r'[.!?]+', text) if s.strip()]
            if sentences:
                sentence_lengths.append(len(words) / len(sentences))
                
            punctuation_count += len(punctuation_regex.findall(text))
            total_chars += len(text)
            
        unique_words = set(all_words)
        vocab_diversity = len(unique_words) / len(all_words) if all_words else 0
        avg_sentence_len = sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0
        avg_word_len = sum(len(w) for w in all_words) / len(all_words) if all_words else 0
        
        # Simple word frequency distribution
        freqs = {}
        for w in all_words:
            if len(w) > 3:  # Skip common short helper words
                freqs[w] = freqs.get(w, 0) + 1
        sorted_freqs = sorted(freqs.items(), key=lambda item: item[1], reverse=True)
        top_tokens = [item[0] for item in sorted_freqs[:5]]
        
        return {
            "avg_word_length": round(avg_word_len, 2),
            "avg_sentence_length": round(avg_sentence_len, 2),
            "punctuation_density": round(punctuation_count / (total_chars + 1e-6), 4),
            "vocabulary_diversity": round(vocab_diversity, 4),
            "top_tokens": top_tokens
        }

class PersonaMirroringService:
    def __init__(self, output_profile_path: str = "./logs/persona_profile.json"):
        self.output_profile_path = output_profile_path
        os.makedirs(os.path.dirname(self.output_profile_path), exist_ok=True)
        self.profile = {}

    async def scrape_public_profile(self, url: str) -> List[str]:
        """Scrapes recent text posts from a given public profile URL."""
        logger.info(f"Targeting public profile: {url}")
        posts = []
        
        if PLAYWRIGHT_AVAILABLE:
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    page = await browser.new_page()
                    # User agent mirroring
                    await page.set_extra_http_headers({
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    })
                    await page.goto(url, wait_until="domcontentloaded")
                    # Generic text extraction selector mapping
                    elements = await page.query_selector_all("p, span.post-text, article")
                    for el in elements[:15]:
                        txt = await el.inner_text()
                        if len(txt.strip()) > 15:
                            posts.append(txt.strip())
                    await browser.close()
            except Exception as e:
                logger.error(f"Playwright scraping failed: {e}. Falling back to simulator.")
                
        # Simulated fallback/testing helper
        if not posts:
            logger.info("Using simulation fallback data for profile scraping...")
            posts = [
                "Building decentralized network protocols today. Security by default is the only way forward.",
                "Why do modern systems bundle so much bloat? Keep it simple, fast, and edge-native.",
                "Working on eBPF telemetry hooks. Rust + Linux kernel is an absolute superpower!",
                "Decentralized state replication: checking out ZeroMQ vs NATS for the mesh topology.",
                "Autonomy does not mean hype. It means local model execution on unprivileged runtimes."
            ]
            
        return posts

    def mirror_style_prompt(self, target_message: str, profile_features: dict) -> str:
        """Adapts a message draft to match the linguistic fingerprint of the target profile."""
        logger.info("Adapting message using persona profile features...")
        
        # Example representation of prompt tailoring
        # In production, this dictionary is fed to an LLM context window
        adapted_prompt = f"""
        [SYSTEM ROLE]
        You are mirroring a target digital persona. Match these writing constraints:
        - Average Word Length: {profile_features['avg_word_length']} characters
        - Average Sentence Length: {profile_features['avg_sentence_length']} words
        - Punctuation Density Index: {profile_features['punctuation_density']}
        - Vocabulary Diversity Index: {profile_features['vocabulary_diversity']}
        - Signature Vocabulary/Tokens: {", ".join(profile_features['top_tokens'])}

        Transform the draft below into the target's writing style.
        
        [DRAFT]
        "{target_message}"
        
        [ADAPTED OUTPUT]
        """
        
        # Simple local rule-based simulation of mirroring for verification
        words = target_message.split()
        if profile_features['avg_sentence_length'] < 10:
            # Shorten sentences
            adapted = " ".join(words[:min(len(words), 8)]) + "."
        else:
            adapted = target_message
            
        # Append some signature tokens if appropriate
        if profile_features['top_tokens']:
            adapted += f" Simple, fast, and {profile_features['top_tokens'][0]}-native."
            
        return adapted

    async def run(self, profile_url: str):
        # 1. Scrape posts
        posts = await self.scrape_public_profile(profile_url)
        logger.info(f"Retrieved {len(posts)} posts for analysis.")
        
        # 2. Extract style profile
        self.profile = IdentityStyleAnalyzer.analyze(posts)
        logger.info(f"Extracted Profile Style Features: {json.dumps(self.profile, indent=2)}")
        
        # Save profile
        with open(self.output_profile_path, 'w', encoding='utf-8') as f:
            json.dump(self.profile, f, indent=2)
            logger.info(f"Persona style signature saved to {self.output_profile_path}")

        # 3. Test style mirroring
        draft = "We should build an automated framework that checks system files without root privileges."
        mirrored = self.mirror_style_prompt(draft, self.profile)
        logger.info(f"Original Draft: '{draft}'")
        logger.info(f"Mirrored Result: '{mirrored}'")

async def main():
    service = PersonaMirroringService()
    await service.run("https://twitter.com/example_dev")

if __name__ == "__main__":
    asyncio.run(main())
