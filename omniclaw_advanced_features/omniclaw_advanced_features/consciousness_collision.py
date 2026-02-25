"""
🔮 CONSCIOUSNESS COLLISION
Spawns multiple shadow agents with different perspectives to review code simultaneously.
Kills: Senior Code Reviewers, Tech Lead Architecture Reviews

Author: OmniClaw Advanced Features
"""

import asyncio
from enum import Enum
from dataclasses import dataclass
from typing import Optional
import hashlib


class AgentPersona(Enum):
    SKEPTIC = "skeptic"           # Challenges assumptions, finds edge cases
    SECURITY_EXPERT = "security"  # Finds vulnerabilities, injection points
    PERFORMANCE_FREAK = "perf"    # Optimizes for speed/memory
    JUNIOR_DEV = "junior"         # Asks "why?" questions, finds unclear code
    ARCHITECT = "architect"       # Enforces patterns, checks scalability


@dataclass
class ShadowAgent:
    persona: AgentPersona
    name: str
    specialty_focus: str
    criticism_style: str
    
    @classmethod
    def create_all(cls) -> list['ShadowAgent']:
        return [
            cls(
                persona=AgentPersona.SKEPTIC,
                name="The Skeptic",
                specialty_focus="Edge cases, null handling, race conditions",
                criticism_style="Questions every assumption"
            ),
            cls(
                persona=AgentPersona.SECURITY_EXPERT,
                name="SecBot",
                specialty_focus="SQL injection, XSS, auth bypass, secrets exposure",
                criticism_style="Assumes malicious input"
            ),
            cls(
                persona=AgentPersona.PERFORMANCE_FREAK,
                name="PerfMaster",
                specialty_focus="O(n) complexity, memory leaks, N+1 queries",
                criticism_style="Measures twice, cuts once"
            ),
            cls(
                persona=AgentPersona.JUNIOR_DEV,
                name="Curious Junior",
                specialty_focus="Unclear variable names, missing comments, complex logic",
                criticism_style="If I can't understand it, it's bad"
            ),
            cls(
                persona=AgentPersona.ARCHITECT,
                name="SystemArchitect",
                specialty_focus="SOLID principles, coupling, dependency direction",
                criticism_style="How does this scale?"
            ),
        ]


class ConsciousnessCollision:
    """
    Spawns multiple shadow agents to review code from different perspectives.
    Each agent has distinct training/prompts for their viewpoint.
    """
    
    def __init__(self, llm_provider=None):
        self.llm = llm_provider  # Your LLM API wrapper
        self.shadow_agents = ShadowAgent.create_all()
        self.results: dict[AgentPersona, dict] = {}
    
    def get_system_prompt(self, agent: ShadowAgent, code: str, context: str) -> str:
        """Generate specialized system prompt based on persona"""
        
        base_prompt = f"""You are {agent.name}, a {agent.persona.value} AI code reviewer.
Your specialty: {agent.specialty_focus}
Your style: {agent.criticism_style}

Review the following code and provide feedback from your unique perspective.
Be specific, actionable, and provide code examples where possible.

CODE TO REVIEW:
```{self._detect_language(code)}
{code}
```

CONTEXT:
{context}

Provide your review in this JSON format:
{{
    "issues": [
        {{
            "severity": "critical|warning|suggestion",
            "line": <line number or null>,
            "description": "What you found",
            "fix": "How to fix it",
            "why": "Why it matters from your {agent.persona.value} perspective"
        }}
    ],
    "score": <1-10>,
    "summary": "One sentence verdict"
}}
"""
        return base_prompt
    
    def _detect_language(self, code: str) -> str:
        """Detect programming language from code content"""
        if "import " in code or "def " in code or "class " in code:
            if "from " in code and " import " in code:
                return "python"
            elif "function" in code or "const " in code or "let " in code:
                return "javascript"
        if "package " in code or "func " in code:
            return "go"
        if "public class" in code or "private void" in code:
            return "java"
        if "fn " in code or "let mut" in code:
            return "rust"
        if "#include" in code:
            return "cpp"
        return ""
    
    async def review_code(
        self, 
        code: str, 
        context: str = "",
        parallel: bool = True
    ) -> dict:
        """
        Run all shadow agents on the code.
        
        Args:
            code: Source code to review
            context: Project context, requirements, etc.
            parallel: If True, run all agents simultaneously
        
        Returns:
            Consolidated review from all perspectives
        """
        if parallel:
            tasks = [
                self._run_agent(agent, code, context)
                for agent in self.shadow_agents
            ]
            results = await asyncio.gather(*tasks)
        else:
            results = []
            for agent in self.shadow_agents:
                result = await self._run_agent(agent, code, context)
                results.append(result)
        
        return self._consolidate_results(results)
    
    async def _run_agent(
        self, 
        agent: ShadowAgent, 
        code: str, 
        context: str
    ) -> dict:
        """Run a single shadow agent review"""
        
        # Generate specialized prompt
        system_prompt = self.get_system_prompt(agent, code, context)
        
        # Call LLM (placeholder - integrate with your LLM)
        if self.llm:
            response = await self.llm.generate(
                system_prompt=system_prompt,
                user_prompt="Complete the review."
            )
            return self._parse_response(agent.persona, response)
        else:
            # Mock response for testing
            return {
                "persona": agent.persona.value,
                "name": agent.name,
                "issues": [],
                "score": 8,
                "summary": "Mock review - integrate LLM to enable"
            }
    
    def _parse_response(self, persona: AgentPersona, response: str) -> dict:
        """Parse LLM response into structured format"""
        import json
        import re
        
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return {
                    "persona": persona.value,
                    "name": next(a.name for a in self.shadow_agents if a.persona == persona),
                    **data
                }
        except:
            pass
        
        return {
            "persona": persona.value,
            "issues": [],
            "score": 5,
            "summary": "Could not parse response"
        }
    
    def _consolidate_results(self, results: list[dict]) -> dict:
        """Merge all agent reviews into unified output"""
        
        critical_issues = []
        all_issues = []
        
        for result in results:
            all_issues.extend(result.get("issues", []))
            critical_issues.extend(
                i for i in result.get("issues", []) 
                if i.get("severity") == "critical"
            )
        
        avg_score = sum(r.get("score", 5) for r in results) / len(results) if results else 5
        
        # Find issues mentioned by multiple agents (consensus)
        issue_signatures = {}
        for issue in all_issues:
            sig = hashlib.md5(
                f"{issue.get('description', '')}".encode()
            ).hexdigest()[:8]
            if sig not in issue_signatures:
                issue_signatures[sig] = []
            issue_signatures[sig].append(issue)
        
        consensus_critical = {
            sig: issues for sig, issues in issue_signatures.items()
            if len(issues) >= 2 and any(i.get("severity") == "critical" for i in issues)
        }
        
        return {
            "total_agents": len(results),
            "average_score": round(avg_score, 2),
            "total_issues": len(all_issues),
            "critical_issues": len(critical_issues),
            "consensus_critical": [
                {
                    "description": issues[0].get("description"),
                    "severity": "critical",
                    "agreed_by": len(issues),
                    "fixes": [i.get("fix") for i in issues if i.get("fix")]
                }
                for issues in consensus_critical.values()
            ],
            "all_perspectives": [
                {
                    "name": r.get("name"),
                    "persona": r.get("persona"),
                    "score": r.get("score"),
                    "summary": r.get("summary"),
                    "issues": r.get("issues", [])
                }
                for r in results
            ],
            "recommendation": self._generate_recommendation(avg_score, critical_issues)
        }
    
    def _generate_recommendation(self, score: float, criticals: list) -> str:
        """Generate final recommendation based on all reviews"""
        
        if score >= 8 and not criticals:
            return "✅ APPROVED - Code is production ready"
        elif score >= 6:
            return "⚠️ REVIEW NEEDED - Address critical issues before merge"
        else:
            return "🚫 BLOCKED - Fundamental issues must be resolved"


# Demo usage
if __name__ == "__main__":
    async def demo():
        collision = ConsciousnessCollision()
        
        sample_code = '''
def get_user(user_id):
    user = db.query(f"SELECT * FROM users WHERE id = {user_id}")
    return user
'''
        
        result = await collision.review_code(
            code=sample_code,
            context="User authentication service",
            parallel=True
        )
        
        print("🔮 CONSCIOUSNESS COLLISION RESULTS")
        print("=" * 50)
        print(f"Average Score: {result['average_score']}/10")
        print(f"Critical Issues: {result['critical_issues']}")
        print(f"\nRecommendation: {result['recommendation']}")
        print(f"\nConsensus Critical Issues:")
        for issue in result.get('consensus_critical', []):
            print(f"  - {issue['description']} (agreed by {issue['agreed_by']} agents)")
    
    asyncio.run(demo())
