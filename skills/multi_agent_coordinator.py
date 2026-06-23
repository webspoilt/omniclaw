import json
import time

from core.skills.registry import tool

_dispatched = {}

@tool()
def assign_task(agent_id: str, task: str, params: str = "{}") -> str:
    """Assign a task to a sub-agent with optional parameters."""
    task_id = f"{agent_id}_{int(time.time())}_{len(_dispatched) + 1}"
    _dispatched[task_id] = {
        "agent_id": agent_id,
        "task": task,
        "params": json.loads(params),
        "status": "assigned",
        "result": None,
        "created": time.time()
    }
    return f"Task {task_id} assigned to {agent_id}: {task[:100]}"


@tool()
def collect_results(task_id: str = "") -> str:
    """Collect results from completed sub-agent tasks."""
    if task_id:
        entry = _dispatched.get(task_id)
        if not entry:
            return f"Task {task_id} not found."
        return f"Agent: {entry['agent_id']} | Status: {entry['status']} | Result: {entry['result'] or 'pending'}"
    if not _dispatched:
        return "No tasks have been dispatched."
    lines = ["=== Task Results ==="]
    for tid, entry in sorted(_dispatched.items()):
        lines.append(f"  {tid}: agent={entry['agent_id']} status={entry['status']}")
        if entry["result"]:
            lines.append(f"    result: {str(entry['result'])[:200]}")
    return "\n".join(lines)


@tool()
def resolve_conflicts(agent_a_result: str, agent_b_result: str, context: str = "") -> str:
    """Resolve conflicts between two sub-agent findings."""
    lines_a = agent_a_result.strip().splitlines()
    lines_b = agent_b_result.strip().splitlines()
    common = set(lines_a) & set(lines_b)
    only_a = set(lines_a) - set(lines_b)
    only_b = set(lines_b) - set(lines_a)
    result = "=== Conflict Resolution ===\n"
    if context:
        result += f"Context: {context[:200]}\n"
    result += f"Agree on {len(common)} items:\n"
    for item in list(common)[:10]:
        result += f"  [OK] {item[:120]}\n"
    if only_a:
        result += f"\nOnly Agent A ({len(only_a)} items):\n"
        for item in list(only_a)[:10]:
            result += f"  [A] {item[:120]}\n"
    if only_b:
        result += f"\nOnly Agent B ({len(only_b)} items):\n"
        for item in list(only_b)[:10]:
            result += f"  [B] {item[:120]}\n"
    result += "\nRecommended: merge common items, review unique per-agent, cross-validate disputed."
    return result


@tool()
def summarize_agent_status() -> str:
    """Summarize all sub-agent tasks and their current status."""
    if not _dispatched:
        return "No sub-agents active."
    statuses = {}
    for tid, entry in _dispatched.items():
        s = entry["status"]
        agent = entry["agent_id"]
        if agent not in statuses:
            statuses[agent] = {"assigned": 0, "completed": 0, "failed": 0, "tasks": []}
        statuses[agent][s if s in ("assigned", "completed", "failed") else "assigned"] += 1
        statuses[agent]["tasks"].append(tid)
    lines = ["=== Sub-agent Status ==="]
    for agent, s in sorted(statuses.items()):
        total = s["assigned"] + s["completed"] + s["failed"]
        lines.append(f"  {agent}: {total} tasks ({s['completed']} done, {s['assigned']} active, {s['failed']} failed)")
    return "\n".join(lines)
