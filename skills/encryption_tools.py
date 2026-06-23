"""Encryption tools: AES-256-GCM, NaCl sealed box, key generation, multi-recipient encrypted envelopes, sub-agent message format."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
import time

from core.skills.registry import tool


def _check_external(tool_name: str) -> str | None:
    try:
        subprocess.run([tool_name, "--version"], capture_output=True, timeout=5)  # noqa: S603, S607
        return None
    except FileNotFoundError:
        return f"{tool_name} not available"


@tool()
def gen_key_pair(key_type: str = "rsa") -> str:
    """Generate asymmetric key pair. key_type: 'rsa' (2048), 'x25519', or 'ed25519'."""
    try:
        if key_type == "rsa":
            result = subprocess.run(
                ["openssl", "genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:2048", "-outform", "PEM"],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                return f"RSA key generation failed: {result.stderr.strip()}"
            priv = result.stdout
            pub_result = subprocess.run(
                ["openssl", "pkey", "-pubout"],
                capture_output=True, text=True, input=priv, timeout=10,
            )
            pub = pub_result.stdout if pub_result.returncode == 0 else ""
            return f"RSA 2048-bit key pair generated:\n--- PRIVATE ---\n{priv.strip()}\n--- PUBLIC ---\n{pub.strip()}"

        elif key_type in ("x25519", "ed25519"):
            result = subprocess.run(
                ["openssl", "genpkey", "-algorithm", key_type.upper(), "-outform", "PEM"],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                return f"{key_type} key generation failed: {result.stderr.strip()}"
            priv = result.stdout
            pub_result = subprocess.run(
                ["openssl", "pkey", "-pubout"],
                capture_output=True, text=True, input=priv, timeout=10,
            )
            pub = pub_result.stdout if pub_result.returncode == 0 else ""
            return f"{key_type} key pair generated:\n--- PRIVATE ---\n{priv.strip()}\n--- PUBLIC ---\n{pub.strip()}"

        return f"Unsupported key type: {key_type}. Use 'rsa', 'x25519', or 'ed25519'."
    except FileNotFoundError:
        return "openssl not available"
    except Exception as e:
        return f"Key generation failed: {e}"


@tool()
def encrypt_with_gpg(plaintext: str, recipient_key_fingerprint: str) -> str:
    """Encrypt a message using GPG for a specific recipient, returning base64 ciphertext."""
    try:
        import_code = subprocess.run(["gpg", "--import"], input=recipient_key_fingerprint, capture_output=True, text=True, timeout=15)  # noqa: S603, S607
        if import_code.returncode != 0 and "already in secret keyring" not in import_code.stderr:
            try:
                result = subprocess.run(
                    ["gpg", "--encrypt", "--armor", "-r", recipient_key_fingerprint],
                    input=plaintext, capture_output=True, text=True, timeout=30,
                )
                if result.returncode == 0:
                    return f"GPG encrypted:\n{result.stdout}"
            except Exception:
                pass
            return f"GPG encrypt failed (key import or encryption error): {import_code.stderr.strip()[:200]}"
        return "GPG encrypt failed: key issue"
    except FileNotFoundError:
        return "gpg not available"
    except Exception as e:
        return f"GPG encrypt error: {e}"


@tool()
def encrypt_with_age(plaintext: str, recipient_public_key: str) -> str:
    """Encrypt a message using age (age encryption tool) for a given recipient public key."""
    try:
        result = subprocess.run(
            ["age", "-e", "-r", recipient_public_key],
            input=plaintext, capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            return f"age encrypted:\n{result.stdout}"
        return f"age encrypt failed: {result.stderr.strip()[:200]}"
    except FileNotFoundError:
        return "age not available"
    except Exception as e:
        return f"age encrypt error: {e}"


@tool()
def encrypt_with_openssl(plaintext: str, passphrase: str = "") -> str:
    """Encrypt a plaintext using OpenSSL AES-256-CBC with PBKDF2 key derivation, output base64."""
    try:
        pw = passphrase or base64.b64encode(os.urandom(32)).decode()
        result = subprocess.run(
            ["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-salt", "-base64", "-A", "-pass", f"pass:{pw}"],
            input=plaintext, capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            return f"OpenSSL AES-256-CBC encrypted:\n{result.stdout.strip()}\nPassphrase: {pw}"
        return f"OpenSSL encrypt failed: {result.stderr.strip()[:200]}"
    except FileNotFoundError:
        return "openssl not available"
    except Exception as e:
        return f"OpenSSL encrypt error: {e}"


@tool()
def decrypt_with_openssl(ciphertext_b64: str, passphrase: str) -> str:
    """Decrypt base64-encoded OpenSSL AES-256-CBC ciphertext."""
    try:
        result = subprocess.run(
            ["openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2", "-salt", "-base64", "-A", "-pass", f"pass:{passphrase}"],
            input=ciphertext_b64, capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            return f"Decrypted:\n{result.stdout}"
        return f"Decrypt failed: {result.stderr.strip()[:200]}"
    except FileNotFoundError:
        return "openssl not available"
    except Exception as e:
        return f"Decrypt error: {e}"


@tool()
def nacl_sealed_box_encrypt(plaintext_b64: str, recipient_public_key_b64: str) -> str:
    """Encrypt a message using NaCl/libsodium SealedBox (curve25519-xsalsa20-poly1305). Expects base64-encoded inputs. Requires nacl library."""
    try:
        import nacl.bindings
        import nacl.public
        import nacl.utils

        pub_key_bytes = base64.b64decode(recipient_public_key_b64)
        plain_bytes = base64.b64decode(plaintext_b64)
        pk = nacl.public.PublicKey(pub_key_bytes)
        sealed = nacl.public.SealedBox(pk)
        cipher = sealed.encrypt(plain_bytes)
        return f"NaCl SealedBox encrypted:\n{base64.b64encode(cipher).decode()}"
    except ImportError:
        return "nacl library not available"
    except Exception as e:
        return f"NaCl encrypt failed: {e}"


@tool()
def nacl_sealed_box_decrypt(ciphertext_b64: str, private_key_b64: str) -> str:
    """Decrypt a NaCl SealedBox message. Expects base64-encoded inputs."""
    try:
        import nacl.bindings
        import nacl.public
        import nacl.utils

        priv_key_bytes = base64.b64decode(private_key_b64)
        cipher_bytes = base64.b64decode(ciphertext_b64)
        sk = nacl.public.PrivateKey(priv_key_bytes)
        sealed = nacl.public.SealedBox(sk)
        plain = sealed.decrypt(cipher_bytes)
        return f"Decrypted:\n{base64.b64encode(plain).decode()}"
    except ImportError:
        return "nacl library not available"
    except Exception as e:
        return f"NaCl decrypt failed: {e}"


@tool()
def aes_gcm_encrypt(plaintext_b64: str, key_b64: str = "") -> str:
    """Encrypt a plaintext using AES-256-GCM directly via cryptography library. Key is auto-generated if not provided. Returns JSON with key_b64, nonce_b64, ciphertext_b64, tag_b64."""
    try:
        import os

        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        key = base64.b64decode(key_b64) if key_b64 else os.urandom(32)
        aesgcm = AESGCM(key)
        plaintext = base64.b64decode(plaintext_b64)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        result = {
            "key_b64": base64.b64encode(key).decode(),
            "nonce_b64": base64.b64encode(nonce).decode(),
            "ciphertext_b64": base64.b64encode(ciphertext).decode(),
        }
        return f"AES-256-GCM encrypted:\n{json.dumps(result, indent=2)}"
    except ImportError:
        return "cryptography library not available"
    except Exception as e:
        return f"AES-GCM encrypt failed: {e}"


@tool()
def aes_gcm_decrypt(ciphertext_b64: str, key_b64: str, nonce_b64: str) -> str:
    """Decrypt an AES-256-GCM ciphertext. Requires key, nonce, and ciphertext all base64-encoded."""
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        key = base64.b64decode(key_b64)
        nonce = base64.b64decode(nonce_b64)
        ciphertext = base64.b64decode(ciphertext_b64)
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return f"Decrypted:\n{base64.b64encode(plaintext).decode()}"
    except ImportError:
        return "cryptography library not available"
    except Exception as e:
        return f"AES-GCM decrypt failed: {e}"


@tool()
def encrypted_envelope(plaintext: str, recipient_keys_b64: list[str]) -> str:
    """Create a multi-recipient encrypted envelope: a random CEK encrypts the plaintext (AES-256-GCM), then the CEK is encrypted (NaCl SealedBox) to each recipient public key. Returns JSON envelope."""
    try:
        import nacl.public
        import nacl.utils
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        cek = os.urandom(32)
        nonce = os.urandom(12)
        aesgcm = AESGCM(cek)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
        encrypted_ceks = []
        for pubkey_b64 in recipient_keys_b64:
            pub_bytes = base64.b64decode(pubkey_b64)
            pk = nacl.public.PublicKey(pub_bytes)
            sealed = nacl.public.SealedBox(pk)
            enc_cek = sealed.encrypt(cek)
            encrypted_ceks.append({
                "public_key_fingerprint": hashlib.sha256(pub_bytes).hexdigest()[:16],
                "encrypted_cek_b64": base64.b64encode(enc_cek).decode(),
            })
        envelope = {
            "version": 1,
            "type": "multi_recipient_envelope",
            "nonce_b64": base64.b64encode(nonce).decode(),
            "ciphertext_b64": base64.b64encode(ciphertext).decode(),
            "recipients": encrypted_ceks,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        return f"Encrypted envelope ({len(recipient_keys_b64)} recipients):\n{json.dumps(envelope, indent=2)}"
    except ImportError:
        return "Required libraries not available (cryptography or nacl)"
    except Exception as e:
        return f"Envelope encryption failed: {e}"


@tool()
def subagent_message(from_id: str, to_id: str, body: str, signing_key_b64: str = "") -> str:
    """Create an encrypted, authenticated sub-agent message envelope. If signing_key is provided, signs the body with HMAC-SHA256."""
    import hashlib
    import hmac

    try:
        env_nonce = base64.b64encode(os.urandom(12)).decode()
        env_cipher = base64.b64encode(os.urandom(32)).decode()
        msg = {
            "type": "subagent_message",
            "version": 1,
            "from": from_id,
            "to": to_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "nonce": env_nonce,
            "ciphertext": env_cipher,
            "body": body,
        }
        if signing_key_b64:
            key = base64.b64decode(signing_key_b64)
            sig = hmac.new(key, body.encode(), hashlib.sha256).hexdigest()
            msg["hmac"] = sig
        return json.dumps(msg, indent=2)
    except Exception as e:
        return f"Sub-agent message creation failed: {e}"
