from dataclasses import dataclass
from typing import List


@dataclass
class Persona:
    name: str
    description: str


PERSONAS: List[Persona] = [
    Persona("Whale", "large investor with significant holdings, concerned about manipulation and liquidity"),
    Persona("Retailer", "small retail investor, emotional, follows trends and news"),
    Persona("Analyst", "technical analyst, focuses on charts, patterns, and indicators"),
    Persona("Trader", "day trader, short-term horizon, uses leverage, quick decisions"),
    Persona("Hodler", "long-term believer, ignores short-term volatility, focuses on fundamentals"),
    Persona("Skeptic", "always bearish, points out risks and potential crashes"),
    Persona("Influencer", "social media personality, pumps or dumps based on hype"),
]
