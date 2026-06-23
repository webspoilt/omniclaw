#!/usr/bin/env python3
"""
yubikey_manager.py - Handles YubiKey HMAC-SHA1 challenge-response for key derivation.
Requires: pip install yubikey-manager cryptography
"""

import hashlib
import logging
import os

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from ykman.device import connect_to_device
from ykman.driver import CCIDDriver

logger = logging.getLogger("YubiKeyManager")

class YubiKeyHandler:
    def __init__(self, slot_id=1):
        """
        Initialize YubiKey connection.
        :param slot_id: The configuration slot to use for HMAC-SHA1 (usually 1 or 2).
        """
        self.slot_id = slot_id
        self.device = None
        self._connect()

    def _connect(self):
        """Establish connection to YubiKey."""
        try:
            # Find first connected YubiKey
            devices = list(connect_to_device())
            if not devices:
                raise RuntimeError("No YubiKey found. Please insert one.")
            self.device = devices[0]
            logger.info(f"Connected to YubiKey: {self.device.name}")
        except Exception as e:
            logger.error(f"Failed to connect to YubiKey: {e}")
            raise

    def generate_challenge(self, size=32) -> bytes:
        """Generate a random challenge."""
        return os.urandom(size)

    def hmac_sha1_response(self, challenge: bytes) -> bytes | None:
        """
        Send challenge to YubiKey's HMAC-SHA1 slot and get response.
        Returns 20-byte HMAC-SHA1 digest.
        """
        try:
            if not self.device:
                self._connect()

            # Use the CCID interface for HMAC-SHA1
            driver = CCIDDriver(self.device)
            driver.open()

            # Select the application
            driver.select_hmac_slot(self.slot_id)

            # Send challenge and get response
            response = driver.send_hmac(challenge)
            driver.close()

            logger.debug("HMAC-SHA1 challenge-response successful")
            return response
        except Exception as e:
            logger.error(f"HMAC-SHA1 failed: {e}")
            return None

    def derive_key(self, challenge: bytes | None = None) -> bytes:
        """
        Derive a 32-byte AES-256 key using YubiKey HMAC.
        Uses HKDF to expand the 20-byte HMAC output to 32 bytes.
        """
        if challenge is None:
            challenge = self.generate_challenge()

        hmac_result = self.hmac_sha1_response(challenge)
        if not hmac_result:
            raise RuntimeError("Failed to get HMAC from YubiKey")

        # Expand 20 bytes to 32 bytes via SHA256 of challenge + response
        combined = challenge + hmac_result
        key = hashlib.sha256(combined).digest()
        return key

    def encrypt_vault_key(self, vault_key: bytes, output_file: str):
        """
        Encrypt the vault's master key with YubiKey-derived key and store it.
        This allows the vault to be unlocked only when the YubiKey is present.
        """
        challenge = self.generate_challenge()
        kek = self.derive_key(challenge)

        # Encrypt vault_key with KEK using AES-256-GCM
        iv = os.urandom(12)
        cipher = Cipher(algorithms.AES(kek), modes.GCM(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(vault_key) + encryptor.finalize()

        # Store challenge + iv + tag + ciphertext
        with open(output_file, 'wb') as f:
            f.write(challenge)
            f.write(iv)
            f.write(encryptor.tag)
            f.write(ciphertext)
        logger.info(f"Vault key encrypted and saved to {output_file}")

    def decrypt_vault_key(self, input_file: str) -> bytes | None:
        """
        Decrypt the vault's master key using YubiKey.
        Returns the master key or None if YubiKey is missing/wrong.
        """
        try:
            with open(input_file, 'rb') as f:
                challenge = f.read(32)
                iv = f.read(12)
                tag = f.read(16)
                ciphertext = f.read()

            kek = self.derive_key(challenge)
            cipher = Cipher(algorithms.AES(kek), modes.GCM(iv, tag), backend=default_backend())
            decryptor = cipher.decryptor()
            vault_key = decryptor.update(ciphertext) + decryptor.finalize()
            logger.info("Vault key successfully decrypted with YubiKey")
            return vault_key
        except Exception as e:
            logger.error(f"Failed to decrypt vault key: {e}")
            return None
