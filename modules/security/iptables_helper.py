#!/usr/bin/env python3
"""
iptables_helper.py — Reads the eBPF attack_map via bpftool and inserts
iptables TPROXY rules to redirect repeat offenders to the shadow shell.
"""

import subprocess
import json
import time
import logging
import struct
import socket

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("IPTablesHelper")

SHADOW_PORT = 2222
THRESHOLD = 5
REDIRECTED = set()  # track already-redirected IPs


def int_to_ip(ip_int: int) -> str:
    """Convert a 32-bit integer (network order) to dotted IP string."""
    return socket.inet_ntoa(struct.pack("!I", ip_int))


def get_attackers() -> list:
    """Dump the eBPF attack_map and return IPs above threshold."""
    try:
        result = subprocess.run(
            ["bpftool", "map", "dump", "name", "attack_map", "-j"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            return []
        entries = json.loads(result.stdout)
        attackers = []
        for entry in entries:
            count = entry.get("value", 0)
            if isinstance(count, list):
                count = count[0] if count else 0
            if count > THRESHOLD:
                ip_int = entry.get("key", 0)
                if isinstance(ip_int, list):
                    ip_int = ip_int[0] if ip_int else 0
                ip = int_to_ip(ip_int)
                attackers.append(ip)
        return attackers
    except Exception as e:
        logger.error(f"bpftool dump failed: {e}")
        return []


def redirect_attacker(ip: str):
    """Insert iptables TPROXY rule to redirect SSH from this IP to shadow shell."""
    if ip in REDIRECTED:
        return
    try:
        subprocess.run([
            "iptables", "-t", "mangle", "-A", "PREROUTING",
            "-s", ip, "-p", "tcp", "--dport", "22",
            "-j", "TPROXY", "--on-port", str(SHADOW_PORT),
            "--on-ip", "127.0.0.1",
        ], check=True, capture_output=True)
        REDIRECTED.add(ip)
        logger.info(f"Redirected {ip} → shadow shell :{SHADOW_PORT}")
    except subprocess.CalledProcessError as e:
        logger.error(f"iptables rule failed for {ip}: {e}")


def main():
    logger.info("iptables helper running — polling attack_map every 10s")
    while True:
        for ip in get_attackers():
            redirect_attacker(ip)
        time.sleep(10)


if __name__ == "__main__":
    main()
