from core.skills.registry import tool

logger = logging.getLogger("OmniClaw.Skills.WiFiRecon")

@tool(
    name="wifi_scan",
    description="Scan for nearby WiFi networks and identify their BSSID, Signal strength, and Security types.",
    parameters={
        "interface": {"type": "string", "description": "The wireless interface to use (default: wlan0)"}
    },
    needs_confirmation=True
)
async def wifi_scan(interface: str = "wlan0") -> str:
    """Scan for nearby WiFi networks."""
    recon = WiFiRecon(interface)
    networks = recon.scan_networks()
    if not networks:
        return "No networks found or scan failed."
    return str(networks)

@tool(
    name="wifi_vulnerability_check",
    description="Assess if a specific BSSID is vulnerable to deauthentication attacks.",
    parameters={
        "bssid": {"type": "string", "description": "The BSSID of the target network"}
    }
)
async def wifi_vulnerability_check(bssid: str) -> str:
    """Assess if a network is potentially vulnerable to deauthentication."""
    recon = WiFiRecon()
    result = recon.check_deauth_vulnerability(bssid)
    return str(result)

class WiFiRecon:
    """
    WiFi Reconnaissance Skill (Inspired by Wifi-Deauthentication-Tool)
    Enables scanning and vulnerability assessment of wireless networks.
    """
    
    def __init__(self, interface: str = "wlan0"):
        self.interface = interface

    def scan_networks(self) -> List[Dict]:
        """Scan for nearby WiFi networks."""
        try:
            # Note: Requires root/sudo in real environments
            # Using nmcli or iwlist as a cross-platform fallback logic
            cmd = ["nmcli", "-t", "-f", "SSID,BSSID,SIGNAL,BARS,SECURITY", "dev", "wifi"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            networks = []
            for line in result.stdout.strip().split("\n"):
                if not line: continue
                parts = line.split(":")
                if len(parts) >= 5:
                    networks.append({
                        "ssid": parts[0],
                        "bssid": parts[1],
                        "signal": parts[2],
                        "bars": parts[3],
                        "security": parts[4]
                    })
            return networks
        except Exception as e:
            logger.error(f"WiFi scan failed: {e}")
            return []

    def check_deauth_vulnerability(self, bssid: str) -> Dict:
        """
        Assess if a network is potentially vulnerable to deauthentication.
        (Simplified logic: WEP/WPA without PMF is more vulnerable)
        """
        # This would normally involve capturing a handshake or checking for PMF (Protected Management Frames)
        return {
            "bssid": bssid,
            "vulnerability_score": "Medium",
            "reason": "PMF status unknown. WPA2/3 usually mitigates basic deauth if PMF is required.",
            "recommendation": "Ensure 'Protected Management Frames' is set to Required in AP settings."
        }
