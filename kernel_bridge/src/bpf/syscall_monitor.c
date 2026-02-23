/*
 * OmniClaw Kernel Bridge - eBPF System Call Monitor
 * Monitors system calls and network activity in real-time
 */

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>

#define MAX_MSG_SIZE 256
#define MAX_PROCESSES 1024
#define MAX_PATH_LEN 256

/* Event types */
enum event_type {
    EVENT_SYSCALL,
    EVENT_FILE,
    EVENT_NETWORK,
    EVENT_PROCESS,
    EVENT_ERROR
};

/* Event structure */
struct event {
    u32 type;
    u32 pid;
    u32 ppid;
    u32 uid;
    u32 gid;
    u64 timestamp;
    u64 syscall_nr;
    s64 ret;
    char comm[16];
    char data[MAX_MSG_SIZE];
};

/* Process info */
struct process_info {
    u32 pid;
    u32 ppid;
    u32 uid;
    u32 gid;
    char comm[16];
    u64 start_time;
    u64 syscall_count;
};

/* Maps */
struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024);  /* 256 KB ring buffer */
} events SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, MAX_PROCESSES);
    __type(key, u32);
    __type(value, struct process_info);
} processes SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, MAX_PROCESSES);
    __type(key, u32);
    __type(value, u64);
} syscall_counts SEC(".maps");

/* Configuration map */
struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 1);
    __type(key, u32);
    __type(value, struct {
        u32 monitor_all;
        u32 monitor_syscalls;
        u32 monitor_files;
        u32 monitor_network;
        u32 target_pid;
    });
} config SEC(".maps");

/* Helper to get current process info */
static __always_inline void get_process_info(struct event *e) {
    struct task_struct *task = (struct task_struct *)bpf_get_current_task();
    
    e->pid = bpf_get_current_pid_tgid() >> 32;
    e->ppid = BPF_CORE_READ(task, real_parent, tgid);
    e->uid = bpf_get_current_uid_gid() >> 32;
    e->gid = bpf_get_current_uid_gid() & 0xFFFFFFFF;
    e->timestamp = bpf_ktime_get_ns();
    
    bpf_get_current_comm(&e->comm, sizeof(e->comm));
}

/* Update process info */
static __always_inline void update_process_info(void) {
    u32 pid = bpf_get_current_pid_tgid() >> 32;
    struct process_info *info = bpf_map_lookup_elem(&processes, &pid);
    
    if (!info) {
        struct process_info new_info = {};
        struct task_struct *task = (struct task_struct *)bpf_get_current_task();
        
        new_info.pid = pid;
        new_info.ppid = BPF_CORE_READ(task, real_parent, tgid);
        new_info.uid = bpf_get_current_uid_gid() >> 32;
        new_info.gid = bpf_get_current_uid_gid() & 0xFFFFFFFF;
        new_info.start_time = bpf_ktime_get_ns();
        bpf_get_current_comm(&new_info.comm, sizeof(new_info.comm));
        
        bpf_map_update_elem(&processes, &pid, &new_info, BPF_ANY);
    }
    
    /* Update syscall count */
    u64 *count = bpf_map_lookup_elem(&syscall_counts, &pid);
    if (count) {
        (*count)++;
    } else {
        u64 initial = 1;
        bpf_map_update_elem(&syscall_counts, &pid, &initial, BPF_ANY);
    }
}

/* Submit event to ring buffer */
static __always_inline void submit_event(struct event *e) {
    bpf_ringbuf_submit(e, 0);
}

/* Generic syscall entry probe */
SEC("tp/raw_syscalls/sys_enter")
int trace_sys_enter(struct trace_event_raw_sys_enter *ctx) {
    u32 zero = 0;
    struct {
        u32 monitor_all;
        u32 monitor_syscalls;
        u32 monitor_files;
        u32 monitor_network;
        u32 target_pid;
    } *cfg = bpf_map_lookup_elem(&config, &zero);
    
    if (!cfg || !cfg->monitor_syscalls)
        return 0;
    
    u32 pid = bpf_get_current_pid_tgid() >> 32;
    
    /* Filter by target PID if specified */
    if (cfg->target_pid && cfg->target_pid != pid)
        return 0;
    
    update_process_info();
    
    struct event *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if (!e)
        return 0;
    
    get_process_info(e);
    e->type = EVENT_SYSCALL;
    e->syscall_nr = ctx->id;
    
    /* Capture arguments based on syscall */
    switch (ctx->id) {
    case __NR_openat:
    case __NR_open:
        bpf_probe_read_user_str(&e->data, sizeof(e->data), (void *)ctx->args[1]);
        break;
    case __NR_execve:
    case __NR_execveat:
        bpf_probe_read_user_str(&e->data, sizeof(e->data), (void *)ctx->args[0]);
        break;
    case __NR_connect:
    case __NR_bind:
        /* Capture socket address info */
        break;
    default:
        __builtin_memset(&e->data, 0, sizeof(e->data));
    }
    
    submit_event(e);
    return 0;
}

/* Generic syscall exit probe */
SEC("tp/raw_syscalls/sys_exit")
int trace_sys_exit(struct trace_event_raw_sys_exit *ctx) {
    u32 zero = 0;
    struct {
        u32 monitor_all;
        u32 monitor_syscalls;
        u32 monitor_files;
        u32 monitor_network;
        u32 target_pid;
    } *cfg = bpf_map_lookup_elem(&config, &zero);
    
    if (!cfg || !cfg->monitor_syscalls)
        return 0;
    
    u32 pid = bpf_get_current_pid_tgid() >> 32;
    
    if (cfg->target_pid && cfg->target_pid != pid)
        return 0;
    
    /* We could track return values here */
    return 0;
}

/* File open probe */
SEC("kprobe/do_filp_open")
int trace_do_filp_open(struct pt_regs *ctx) {
    u32 zero = 0;
    struct {
        u32 monitor_all;
        u32 monitor_syscalls;
        u32 monitor_files;
        u32 monitor_network;
        u32 target_pid;
    } *cfg = bpf_map_lookup_elem(&config, &zero);
    
    if (!cfg || !cfg->monitor_files)
        return 0;
    
    u32 pid = bpf_get_current_pid_tgid() >> 32;
    
    if (cfg->target_pid && cfg->target_pid != pid)
        return 0;
    
    struct event *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if (!e)
        return 0;
    
    get_process_info(e);
    e->type = EVENT_FILE;
    
    /* Try to capture filename from path */
    struct filename *name = (struct filename *)PT_REGS_PARM2(ctx);
    if (name) {
        bpf_probe_read_kernel_str(&e->data, sizeof(e->data), (void *)name->name);
    }
    
    submit_event(e);
    return 0;
}

/* Network send probe */
SEC("kprobe/tcp_sendmsg")
int trace_tcp_sendmsg(struct pt_regs *ctx) {
    u32 zero = 0;
    struct {
        u32 monitor_all;
        u32 monitor_syscalls;
        u32 monitor_files;
        u32 monitor_network;
        u32 target_pid;
    } *cfg = bpf_map_lookup_elem(&config, &zero);
    
    if (!cfg || !cfg->monitor_network)
        return 0;
    
    u32 pid = bpf_get_current_pid_tgid() >> 32;
    
    if (cfg->target_pid && cfg->target_pid != pid)
        return 0;
    
    struct event *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if (!e)
        return 0;
    
    get_process_info(e);
    e->type = EVENT_NETWORK;
    
    /* Capture network info */
    struct sock *sk = (struct sock *)PT_REGS_PARM1(ctx);
    size_t size = (size_t)PT_REGS_PARM3(ctx);
    
    bpf_snprintf(e->data, sizeof(e->data), "tcp_send: size=%d", &size, sizeof(size));
    
    submit_event(e);
    return 0;
}

/* Network receive probe */
SEC("kprobe/tcp_recvmsg")
int trace_tcp_recvmsg(struct pt_regs *ctx) {
    u32 zero = 0;
    struct {
        u32 monitor_all;
        u32 monitor_syscalls;
        u32 monitor_files;
        u32 monitor_network;
        u32 target_pid;
    } *cfg = bpf_map_lookup_elem(&config, &zero);
    
    if (!cfg || !cfg->monitor_network)
        return 0;
    
    u32 pid = bpf_get_current_pid_tgid() >> 32;
    
    if (cfg->target_pid && cfg->target_pid != pid)
        return 0;
    
    struct event *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if (!e)
        return 0;
    
    get_process_info(e);
    e->type = EVENT_NETWORK;
    
    bpf_snprintf(e->data, sizeof(e->data), "tcp_recv", NULL, 0);
    
    submit_event(e);
    return 0;
}

/* Process fork probe */
SEC("tp/sched/sched_process_fork")
int trace_sched_process_fork(struct trace_event_raw_sched_process_fork *ctx) {
    u32 zero = 0;
    struct {
        u32 monitor_all;
        u32 monitor_syscalls;
        u32 monitor_files;
        u32 monitor_network;
        u32 target_pid;
    } *cfg = bpf_map_lookup_elem(&config, &zero);
    
    if (!cfg || !cfg->monitor_all)
        return 0;
    
    struct event *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if (!e)
        return 0;
    
    e->type = EVENT_PROCESS;
    e->pid = ctx->child_pid;
    e->ppid = ctx->parent_pid;
    e->timestamp = bpf_ktime_get_ns();
    
    bpf_probe_read_kernel_str(&e->comm, sizeof(e->comm), ctx->child_comm);
    
    bpf_snprintf(e->data, sizeof(e->data), "fork from pid=%d", &ctx->parent_pid, sizeof(ctx->parent_pid));
    
    submit_event(e);
    return 0;
}

/* Process exit probe */
SEC("tp/sched/sched_process_exit")
int trace_sched_process_exit(struct trace_event_raw_sched_process_template *ctx) {
    u32 zero = 0;
    struct {
        u32 monitor_all;
        u32 monitor_syscalls;
        u32 monitor_files;
        u32 monitor_network;
        u32 target_pid;
    } *cfg = bpf_map_lookup_elem(&config, &zero);
    
    if (!cfg || !cfg->monitor_all)
        return 0;
    
    u32 pid = bpf_get_current_pid_tgid() >> 32;
    
    /* Clean up process tracking */
    bpf_map_delete_elem(&processes, &pid);
    bpf_map_delete_elem(&syscall_counts, &pid);
    
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
