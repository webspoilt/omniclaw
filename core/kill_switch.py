# core/kill_switch.py — Global emergency halt for OmniClaw
"""
All modules MUST call check_kill_switch() before executing
any autonomous shell command or destructive action.
"""

KILL_SWITCH = False  # Set to True to halt all autonomous operations


def check_kill_switch():
    """Raise RuntimeError if the global kill switch is active."""
    if KILL_SWITCH:
        raise RuntimeError("🛑 Global kill switch activated — all autonomous actions halted!")


def activate():
    """Activate the kill switch."""
    global KILL_SWITCH
    KILL_SWITCH = True


def deactivate():
    """Deactivate the kill switch."""
    global KILL_SWITCH
    KILL_SWITCH = False
