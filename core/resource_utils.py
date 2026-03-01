# resource_utils.py — Common Resource-Awareness Helper for OmniClaw
"""
All modules import resource_check() to gate heavy operations
on battery, CPU, and memory constraints — especially on mobile.
"""

import logging

logger = logging.getLogger("ResourceUtils")

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


def resource_check(
    min_battery: int = 20,
    max_cpu: int = 70,
    max_memory: int = 80,
    is_mobile: bool = True,
) -> bool:
    """
    Returns True if the system has enough resources to proceed.
    On desktop (is_mobile=False) we always return True.
    """
    if not is_mobile:
        return True

    if not HAS_PSUTIL:
        logger.warning("psutil not installed — skipping resource check")
        return True

    # Battery
    battery = psutil.sensors_battery()
    if battery and battery.percent < min_battery and not battery.power_plugged:
        logger.warning(f"Low battery ({battery.percent}%), aborting.")
        return False

    # CPU
    cpu = psutil.cpu_percent(interval=1)
    if cpu > max_cpu:
        logger.warning(f"CPU too high ({cpu}%), aborting.")
        return False

    # Memory
    mem = psutil.virtual_memory().percent
    if mem > max_memory:
        logger.warning(f"Memory too high ({mem}%), aborting.")
        return False

    return True
