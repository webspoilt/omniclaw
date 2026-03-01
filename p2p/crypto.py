"""
crypto.py — AES-256-GCM encryption helpers for the P2P module.
Shared by p2p_network.py and any other module needing encrypted comms.
"""

import base64

try:
    from Cryptodome.Cipher import AES
except ImportError:
    from Crypto.Cipher import AES


class AESCipher:
    """AES-256-GCM: nonce(16) + ciphertext + tag(16)."""

    def __init__(self, key: bytes):
        if len(key) != 32:
            raise ValueError("Key must be exactly 32 bytes")
        self.key = key

    @classmethod
    def from_base64(cls, b64_key: str) -> "AESCipher":
        return cls(base64.b64decode(b64_key))

    def encrypt(self, data: bytes) -> bytes:
        cipher = AES.new(self.key, AES.MODE_GCM)
        ct, tag = cipher.encrypt_and_digest(data)
        return cipher.nonce + ct + tag

    def decrypt(self, enc: bytes) -> bytes:
        nonce, tag = enc[:16], enc[-16:]
        ct = enc[16:-16]
        cipher = AES.new(self.key, AES.MODE_GCM, nonce=nonce)
        return cipher.decrypt_and_verify(ct, tag)
