"""
OmniClaw PentAGI Module
Provides access to the PentAGI autonomous penetration testing framework.
"""

from .client import PentagiClient
from .launcher import PentagiLauncher

__all__ = [
    "PentagiClient",
    "PentagiLauncher"
]
