import logging
import threading
import time

logger = logging.getLogger("OmniClaw.eBPFMonitor")

# eBPF C program to trace execve (process creation)
bpf_text = """
#include <uapi/linux/ptrace.h>
#include <linux/sched.h>
#include <linux/fs.h>

BPF_PERF_OUTPUT(events);

struct data_t {
    u32 pid;
    char comm[TASK_COMM_LEN];
};

int syscall__execve(struct pt_regs *ctx) {
    struct data_t data = {};
    data.pid = bpf_get_current_pid_tgid() >> 32;
    bpf_get_current_comm(&data.comm, sizeof(data.comm));
    events.perf_submit(ctx, &data, sizeof(data));
    return 0;
}
"""

class EBPFMonitor:
    """
    Shadow Kernel eBPF Monitor.
    Hooks into Linux sys_calls (like execve) to detect anomalies.
    Gracefully degrades on non-Linux or non-root systems.
    """
    def __init__(self):
        self.bpf = None
        self.running = False
        self.alerts = []
        self.thread = None
        
        try:
            from bcc import BPF
            self.bpf = BPF(text=bpf_text)
            # Attach to the execve syscall
            execve_fnname = self.bpf.get_syscall_fnname("execve")
            self.bpf.attach_kprobe(event=execve_fnname, fn_name="syscall__execve")
            self.bpf["events"].open_perf_buffer(self._print_event)
            logger.info("eBPF Monitor initialized successfully.")
        except ImportError:
            logger.warning("BCC not installed or unsupported OS. EBPFMonitor running in simulation mode.")
        except Exception as e:
            logger.warning(f"Failed to initialize eBPF (requires root & linux): {e}. Running in simulation mode.")

    def _print_event(self, cpu, data, size):
        if not self.bpf:
            return
        event = self.bpf["events"].event(data)
        cmd = event.comm.decode('utf-8', 'replace')
        
        # Simple alert logic - e.g. flagging suspicious commands
        if cmd in ["nc", "nmap", "curl", "wget", "bash"]:
            alert = f"[Shadow Kernel Alert] Suspicious process started: PID {event.pid}, Command: {cmd}"
            self.alerts.append(alert)
            logger.warning(alert)
            
        # Keep alerts list bounded
        if len(self.alerts) > 50:
            self.alerts.pop(0)

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.thread.start()

    def _poll_loop(self):
        while self.running:
            if self.bpf:
                try:
                    self.bpf.perf_buffer_poll()
                except Exception as e:
                    logger.error(f"eBPF polling error: {e}")
                    time.sleep(1)
            else:
                # Simulation mode
                time.sleep(60)

    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)

    def get_recent_alerts(self, count=10) -> list:
        if not self.bpf:
            return ["eBPF Monitor is in simulation mode (BCC unavailable or no root privileges). No real alerts."]
        return self.alerts[-count:]

# Singleton instance
ebpf_monitor = EBPFMonitor()
