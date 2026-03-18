#!/usr/bin/env python3
"""
create_zero_day_vault.py – Creates an encrypted zero‑day vault.
Run after YubiKey setup.
"""

import os
import sys
import json
import base64
from pathlib import Path

# Add parent directory to path so we can import core modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.security.yubikey_manager import YubiKeyHandler
from core.security.secure_config import OffensiveConfigLoader

def main():
    # Paths
    vault_dir = Path("modules/security/encrypted_vault")
    vault_dir.mkdir(exist_ok=True)
    vault_file = vault_dir / "zero_day_vault.json.aes"
    vault_key_file = Path("config/vault_key.enc")  # created by setup script

    # Check if vault already exists
    if vault_file.exists():
        overwrite = input(f"{vault_file} already exists. Overwrite? (y/N): ")
        if overwrite.lower() != 'y':
            print("Aborted.")
            return

    # We need the master key from the YubiKey to encrypt the vault.
    # The master key is stored encrypted in vault_key_file.
    # We'll reuse the OffensiveConfigLoader to get the vault key.
    loader = OffensiveConfigLoader()
    if not loader.unlock_vault(str(vault_key_file)):
        print("Failed to unlock vault key. Is YubiKey inserted?")
        return

    # Now we have loader.vault_key (the master key)
    # Create an empty vault structure
    empty_vault = {
        "exploits": [
            {
                "name": "example_exploit_CVE-2024-XXXX",
                "target_service": "ssh",
                "code": "print('This is a placeholder exploit. Replace with real code.')"
            }
        ],
        "metadata": {
            "created": time.ctime(),
            "description": "Encrypted zero‑day vault for OmniClaw SOS"
        }
    }

    # Convert to JSON bytes
    vault_json = json.dumps(empty_vault, indent=2).encode('utf-8')

    # Encrypt using the vault key (AES-256-GCM)
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
    import os

    iv = os.urandom(12)
    cipher = Cipher(algorithms.AES(loader.vault_key), modes.GCM(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(vault_json) + encryptor.finalize()
    tag = encryptor.tag

    # Write to file: iv (12) + tag (16) + ciphertext
    with open(vault_file, 'wb') as f:
        f.write(iv)
        f.write(tag)
        f.write(ciphertext)

    print(f"Empty zero‑day vault created at {vault_file}")
    print("You can now replace the placeholder exploit with real code (re‑encrypt by running this script again).")

if __name__ == "__main__":
    import time
    main()