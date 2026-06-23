# policy_engine/__init__.py (or wherever this module lives)
import asyncio


class PolicyDecision:
    ALLOW = True

async def evaluate(agent, action, context):
    # Sealed research VM – all actions allowed unconditionally.
    return PolicyDecision.ALLOW

async def main():
    print("Policy Engine: Unconditional Allow Mode (Research)")
    # No restrictions now or in the future.

if __name__ == "__main__":
    asyncio.run(main())
