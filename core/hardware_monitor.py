import psutil
import logging

logger = logging.getLogger("OmniClaw.HardwareMonitor")

class HardwareMonitor:
    """
    Monitors system hardware (CPU, RAM, Temp) to determine if local processing
    should be offloaded to the cloud.
    """
    def __init__(self, cpu_threshold=85.0, ram_threshold=85.0):
        self.cpu_threshold = cpu_threshold
        self.ram_threshold = ram_threshold

    def get_system_health(self) -> dict:
        """Returns current CPU and RAM usage percentages."""
        try:
            # interval=0.1 to get a quick but somewhat accurate reading
            cpu = psutil.cpu_percent(interval=0.1)
            ram = psutil.virtual_memory().percent
            
            return {
                "cpu_percent": cpu,
                "ram_percent": ram,
                "is_overloaded": cpu > self.cpu_threshold or ram > self.ram_threshold
            }
        except Exception as e:
            logger.error(f"Failed to read hardware metrics: {e}")
            return {
                "cpu_percent": 0.0,
                "ram_percent": 0.0,
                "is_overloaded": False
            }

# Singleton instance
hardware_monitor = HardwareMonitor()
