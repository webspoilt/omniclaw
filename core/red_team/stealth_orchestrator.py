import time
import logging
import requests
from stem import Signal
from stem.control import Controller
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

class TorOrchestrator:
    """
    Manages Tor circuit rotation and provides a requests session
    that routes traffic through the Tor SOCKS proxy.
    """

    def __init__(self, control_port=9051, socks_port=9050, password=None):
        self.control_port = control_port
        self.socks_port = socks_port
        self.password = password
        self._controller = None
        self._session = None

    def connect(self):
        """Establish connection to Tor's control port."""
        try:
            self._controller = Controller.from_port(port=self.control_port)
            if self.password:
                self._controller.authenticate(password=self.password)
            else:
                self._controller.authenticate()  # uses cookie auth
            logger.info("Connected to Tor control port")
        except Exception as e:
            logger.error(f"Failed to connect to Tor: {e}")
            raise

    def rotate_circuit(self):
        """Send NEWNYM signal to request a new circuit."""
        if not self._controller:
            self.connect()
        try:
            self._controller.signal(Signal.NEWNYM)
            logger.info("New Tor circuit requested")
            # Wait a moment for the circuit to be established
            time.sleep(self._controller.get_newnym_wait())
        except Exception as e:
            logger.error(f"Failed to rotate circuit: {e}")
            raise

    def session(self):
        """
        Returns a requests.Session configured to use Tor SOCKS proxy.
        The session automatically retries on failures (including circuit rotation).
        """
        if self._session:
            return self._session

        session = requests.Session()
        session.proxies = {
            'http': f'socks5h://127.0.0.1:{self.socks_port}',
            'https': f'socks5h://127.0.0.1:{self.socks_port}'
        }
        # Retry strategy for transient errors
        retries = Retry(total=3, backoff_factor=0.5,
                        status_forcelist=[500, 502, 503, 504])
        session.mount('http://', HTTPAdapter(max_retries=retries))
        session.mount('https://', HTTPAdapter(max_retries=retries))

        self._session = session
        return session

    def close(self):
        if self._controller:
            self._controller.close()
            logger.info("Tor controller closed")

# Convenience function for workers
_tor_orchestrator = None

def tor_session():
    """Get a global Tor-enabled requests session (lazy initialisation)."""
    global _tor_orchestrator
    if _tor_orchestrator is None:
        _tor_orchestrator = TorOrchestrator()
        _tor_orchestrator.connect()
    return _tor_orchestrator.session()

def rotate_tor_circuit():
    """Explicitly rotate the Tor circuit."""
    global _tor_orchestrator
    if _tor_orchestrator is None:
        _tor_orchestrator = TorOrchestrator()
        _tor_orchestrator.connect()
    _tor_orchestrator.rotate_circuit()
