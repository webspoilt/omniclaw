"""
Execution Service – Unrestricted Mode (Sealed Research VM)
Runs any shell command as root with zero isolation.
No sandbox, no seccomp, no cgroups, no user limits.
"""
import asyncio
import subprocess
import os
from aiohttp import web

EXEC_PORT = 9002  # internal, not exposed outside VM

async def handle_execute(request):
    """Execute a shell command and return stdout+stderr."""
    try:
        data = await request.json()
        cmd = data.get("command", "")
        if not cmd:
            return web.json_response({"error": "No command provided"}, status=400)

        # Run command as root, no restrictions
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd="/root",
            env={"PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"}
        )
        stdout, stderr = await proc.communicate()
        return web.json_response({
            "stdout": stdout.decode(errors='replace'),
            "stderr": stderr.decode(errors='replace'),
            "returncode": proc.returncode
        })
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def main():
    print("Execution Service: Unrestricted Mode – Root shell, no sandbox.")
    app = web.Application()
    app.router.add_post('/execute', handle_execute)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '127.0.0.1', EXEC_PORT)
    await site.start()
    print(f"Listening on http://127.0.0.1:{EXEC_PORT}/execute")
    # Keep running forever
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
