from core.skills.registry import tool

logger = logging.getLogger("OmniClaw.Skills.InjectionAuditor")

@tool(
    name="get_security_payloads",
    description="Retrieve standardized security payloads (XSS, SQLi, SSRF, LFI) for vulnerability testing.",
    parameters={
        "category": {"type": "string", "description": "The category of payloads (xss, sqli, ssrf, lfi)"}
    }
)
async def get_security_payloads(category: str) -> str:
    """Retrieve security payloads."""
    auditor = InjectionAuditor()
    payloads = auditor.get_payloads(category)
    return str(payloads)

@tool(
    name="generate_injection_plan",
    description="Generate a structured testing plan for identifying injection vulnerabilities on a target URL.",
    parameters={
        "target_url": {"type": "string", "description": "The target URL to analyze"},
        "params": {"type": "array", "items": {"type": "string"}, "description": "List of parameters to test"}
    }
)
async def generate_injection_plan(target_url: str, params: list[str]) -> str:
    """Generate injection test plan."""
    auditor = InjectionAuditor()
    plan = auditor.recommend_test_plan(target_url, params)
    return str(plan)

class InjectionAuditor:
    """
    Injection Auditor Skill (Inspired by CyberInject)
    Provides agents with payloads and testing logic for web injections.
    """
    
    def __init__(self):
        self.payload_file = Path(__file__).parent / "payloads.json"
        self.payloads = self._load_payloads()

    def _load_payloads(self) -> Dict[str, List[str]]:
        try:
            with open(self.payload_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load payloads: {e}")
            return {}

    def get_payloads(self, category: str) -> List[str]:
        """Retrieve payloads for a specific vulnerability category."""
        return self.payloads.get(category.lower(), [])

    def recommend_test_plan(self, target_url: str, params: List[str]) -> Dict:
        """Generate a basic injection test plan for a target."""
        return {
            "target": target_url,
            "vulnerability_types": ["XSS", "SQLi"],
            "parameters": params,
            "strategy": "Sequential payload injection into each parameter to observe DOM/SQL leakage.",
            "safe_check": "Always use non-destructive payloads (e.g., alert(1) or SLEEP(1)) first."
        }
