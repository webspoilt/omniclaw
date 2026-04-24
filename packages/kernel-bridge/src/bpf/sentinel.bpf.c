#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

char LICENSE[] SEC("license") = "GPL";

SEC("tp/syscalls/sys_enter_execve")
int handle_execve(struct trace_event_raw_sys_enter *ctx) {
    char comm[16];
    bpf_get_current_comm(&comm, sizeof(comm));

    // Detection logic for common EDR/Security tools
    // If "defender", "crowdstrike", etc. are found, signal the Hive
    
    bpf_printk("Sovereign Sentinel: execve detected from %s\n", comm);
    
    return 0;
}
