import random
import time
import threading
import queue
import requests
from stem import Signal
from stem.control import Controller
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

class TorHive:
    """
    Manages multiple Tor circuits (each on a different SOCKS port) and provides
    a round‑robin of unique IPs for worker agents.
    """

    # Common user agents for rotation
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
    ]

    def __init__(self, num_circuits: int = 5, tor_data_dir: str = "./tor_data",
                 control_port_base: int = 9051, socks_port_base: int = 9050):
        self.num_circuits = num_circuits
        self.tor_data_dir = tor_data_dir
        self.control_port_base = control_port_base
        self.socks_port_base = socks_port_base
        self.circuits = []  # list of (control_port, socks_port, controller)
        self.proxy_queue = queue.Queue()

        self._launch_circuits()
        self._start_refresh_thread()

    def _launch_circuits(self):
        """Launch multiple Tor instances with different ports."""
        for i in range(self.num_circuits):
            control_port = self.control_port_base + i
            socks_port = self.socks_port_base + i
            data_dir = f"{self.tor_data_dir}/tor_{i}"
            config = {
                "SocksPort": str(socks_port),
                "ControlPort": str(control_port),
                "DataDirectory": data_dir,
                "CookieAuthentication": "1",
            }
            # Launch Tor process (or connect to existing)
            # In production, you might use launch_tor_with_config from stem
            # For simplicity, assume Tor is already running with these ports.
            # We'll just connect via Controller.
            try:
                controller = Controller.from_port(port=control_port)
                controller.authenticate()
                self.circuits.append((control_port, socks_port, controller))
                self.proxy_queue.put(socks_port)
                logger.info(f"Circuit {i} ready (SOCKS {socks_port})")
            except Exception as e:
                logger.error(f"Failed to connect to Tor on port {control_port}: {e}")

    def _refresh_circuit(self, socks_port: int, controller: Controller):
        """Request new identity for a circuit and requeue it."""
        try:
            controller.signal(Signal.NEWNYM)
            time.sleep(controller.get_newnym_wait())
            self.proxy_queue.put(socks_port)
        except Exception as e:
            logger.error(f"Failed to refresh circuit on port {socks_port}: {e}")
            # Put it back anyway
            self.proxy_queue.put(socks_port)

    def _start_refresh_thread(self):
        """Periodically refresh circuits to keep IPs rotating."""
        def refresher():
            while True:
                time.sleep(60)  # refresh every minute
                for control_port, socks_port, controller in self.circuits:
                    # Remove from queue, refresh, then put back
                    # To avoid blocking, we could refresh in a separate thread
                    threading.Thread(target=self._refresh_circuit,
                                     args=(socks_port, controller)).start()
        thread = threading.Thread(target=refresher, daemon=True)
        thread.start()

    def get_proxy_session(self) -> requests.Session:
        """
        Returns a requests.Session configured with a random SOCKS proxy from the pool
        and randomised headers.
        """
        socks_port = self.proxy_queue.get()  # blocks until available
        session = requests.Session()
        session.proxies = {
            'http': f'socks5h://127.0.0.1:{socks_port}',
            'https': f'socks5h://127.0.0.1:{socks_port}'
        }
        # Random headers
        session.headers.update({
            'User-Agent': random.choice(self.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': random.choice(['en-US,en;q=0.5', 'fr-FR,fr;q=0.9', 'de-DE,de;q=0.7']),
            'DNT': str(random.randint(0, 1)),
            'Connection': 'keep-alive',
        })
        # After using, put the port back into queue (or handle in a context manager)
        # For simplicity, we don't auto-return; caller must return it.
        return session, socks_port

    def return_proxy(self, socks_port: int):
        """Return a proxy port to the pool after use."""
        self.proxy_queue.put(socks_port)

# Example usage in a worker
if __name__ == "__main__":
    hive = TorHive(num_circuits=3)
    session, port = hive.get_proxy_session()
    try:
        r = session.get("http://httpbin.org/ip")
        print(r.json())
    finally:
        hive.return_proxy(port)
