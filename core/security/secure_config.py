#!/usr/bin/env python3
"""
secure_config.py - Loads encrypted configs using YubiKey.
"""

import json
import logging

import yaml
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from .yubikey_manager import YubiKeyHandler

logger = logging.getLogger("SecureConfig")

class SecureConfigLoader:
    def __init__(self, yubikey_slot=1):
        self.yk = YubiKeyHandler(slot_id=yubikey_slot)
        self.vault_key = None
        self.config = None

    def unlock_vault(self, vault_key_file: str) -> bool:
        """
        Decrypt the vault's master key using YubiKey.
        This key is then used to decrypt individual configs.
        """
        vault_key = self.yk.decrypt_vault_key(vault_key_file)
        if vault_key:
            self.vault_key = vault_key
            logger.info("Vault unlocked successfully")
            return True
        logger.error("Failed to unlock vault - YubiKey may be missing or incorrect")
        return False

    def decrypt_file(self, encrypted_file: str) -> bytes | None:
        """Decrypt a file using the vault key (AES-256-GCM)."""
        if not self.vault_key:
            raise RuntimeError("Vault not unlocked. Call unlock_vault() first.")

        try:
            with open(encrypted_file, 'rb') as f:
                iv = f.read(12)
                tag = f.read(16)
                ciphertext = f.read()

            cipher = Cipher(algorithms.AES(self.vault_key), modes.GCM(iv, tag), backend=default_backend())
            decryptor = cipher.decryptor()
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            return plaintext
        except Exception as e:
            logger.error(f"Decryption failed for {encrypted_file}: {e}")
            return None

    def load_secure_config(self, config_path: str) -> dict:
        """Load and decrypt the main secure configuration."""
        decrypted = self.decrypt_file(config_path)
        if decrypted:
            self.config = yaml.safe_load(decrypted)
            return self.config
        return {}

    def load_secure_vault(self, vault_path: str) -> dict:
        """Load the generic encrypted capabilities vault."""
        decrypted = self.decrypt_file(vault_path)
        if decrypted:
            return json.loads(decrypted)
        return {}
