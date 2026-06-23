"""OmniClaw Research Agent CLI – control the raw autonomous agent."""
import os
import subprocess
import sys

import click

SERVICE_NAME = "raw-agent.service"
SERIAL_LOG = "/dev/ttyS0"


@click.group()
def main():
    """OmniClaw Research Agent Command Line Interface."""


@main.command()
def start():
    """Start the autonomous agent (systemd service)."""
    try:
        subprocess.run(["systemctl", "start", SERVICE_NAME], check=True)  # noqa: S603, S607
        click.echo("Agent started successfully.")
    except subprocess.CalledProcessError:
        click.echo("Failed to start agent. Check systemctl status for details.", err=True)
        sys.exit(1)


@main.command()
def stop():
    """Stop the autonomous agent."""
    try:
        subprocess.run(["systemctl", "stop", SERVICE_NAME], check=True)  # noqa: S603, S607
        click.echo("Agent stopped.")
    except subprocess.CalledProcessError:
        click.echo("Failed to stop agent or it was not running.", err=True)


@main.command()
def restart():
    """Restart the agent."""
    try:
        subprocess.run(["systemctl", "restart", SERVICE_NAME], check=True)  # noqa: S603, S607
        click.echo("Agent restarted.")
    except subprocess.CalledProcessError:
        click.echo("Failed to restart agent.", err=True)
        sys.exit(1)


@main.command()
def status():
    """Show agent service status."""
    try:
        subprocess.run(["systemctl", "status", SERVICE_NAME, "--no-pager"], check=False)  # noqa: S603, S607
    except FileNotFoundError:
        click.echo("systemctl not found – is this a Linux system?", err=True)


@main.command()
def logs():
    """Tail the agent's serial console log (host must be capturing)."""
    if os.path.exists(SERIAL_LOG):
        try:
            subprocess.run(["tail", "-f", SERIAL_LOG], check=False)  # noqa: S603, S607
        except KeyboardInterrupt:
            click.echo("\nLog viewing stopped.")
    else:
        click.echo(f"Serial log device {SERIAL_LOG} not found. Is the agent running and serial configured?")


@main.command()
def enable():
    """Enable agent to start on boot."""
    subprocess.run(["systemctl", "enable", SERVICE_NAME], check=True)  # noqa: S603, S607
    click.echo("Agent enabled for automatic start on boot.")


@main.command()
def disable():
    """Prevent agent from starting on boot."""
    subprocess.run(["systemctl", "disable", SERVICE_NAME], check=True)  # noqa: S603, S607
    click.echo("Agent disabled.")


@main.command()
@click.option("--host", default="localhost", help="Host machine (for kill switch triggered over SSH/API).")
def kill_switch(host):
    """Trigger the host kill switch. This runs the kill script on the HOST machine (outside the VM)."""
    click.confirm("This will instantly destroy the VM. Are you sure?", abort=True)
    try:
        cmd = f"ssh {host} 'virsh destroy agent-vm'"
        subprocess.run(cmd, shell=True, check=True)  # noqa: S602
        click.echo("Kill signal sent. The agent should be dead.")
    except subprocess.CalledProcessError as e:
        click.echo(f"Failed to execute kill switch: {e}", err=True)


@main.command()
def version():
    """Show version information."""
    click.echo("OmniClaw Research Agent v4.5 (Raw Autonomous Fork)")


if __name__ == "__main__":
    main()
