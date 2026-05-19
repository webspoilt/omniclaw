#include <uapi/linux/ptrace.h>
#include <linux/sched.h>
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

struct forensic_event {
    u32 pid;
    u64 pc;      // Program counter
    u64 sp;      // Stack pointer
    char comm[16];
    u8 memory_snippet[64];
};

struct {
    __uint(type, BPF_MAP_TYPE_PERF_EVENT_ARRAY);
    __uint(max_entries, 1024);
} forensics_rb SEC(".maps");

SEC("kprobe/do_exit")
int bpf_prog_snapshot(struct pt_regs *ctx) {
    struct task_struct *task = (struct task_struct *)bpf_get_current_task();
    struct forensic_event evt = {};
    
    evt.pid = bpf_get_current_pid_tgid() >> 32;
    bpf_get_current_comm(&evt.comm, sizeof(evt.comm));
    evt.pc = PT_REGS_IP(ctx);
    evt.sp = PT_REGS_SP(ctx);
    
    // Read user stack snippet
    bpf_probe_read_user(&evt.memory_snippet, sizeof(evt.memory_snippet), (void*)evt.sp);
    
    // Output forensic capsule to user daemon via perf ring buffer
    bpf_perf_event_output(ctx, &forensics_rb, BPF_F_CURRENT_CPU, &evt, sizeof(evt));
    
    return 0;
}

char _license[] SEC("license") = "GPL";
