/*
 * OmniClaw IPS — eBPF Intrusion Prevention Monitor
 * ==================================================
 * Traces tcp_v4_connect and SSH authentication attempts.
 * Counts per-IP failed logins and emits ring-buffer alerts
 * when a configurable threshold is exceeded.
 *
 * Compile:  clang -O2 -g -target bpf -D__TARGET_ARCH_x86_64 \
 *           -I/usr/include/x86_64-linux-gnu -c monitor.bpf.c -o monitor.bpf.o
 *
 * Copyright (c) 2026 OmniClaw Project — GPL-2.0
 */

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>
#include <bpf/bpf_endian.h>

/* ──────────────────────── Constants ──────────────────────── */

#define MAX_TRACKED_IPS   4096
#define SSH_PORT          22
#define MAX_DATA_LEN      128

/* Alert types */
#define ALERT_TCP_CONNECT       1   /* New TCP connection observed        */
#define ALERT_SSH_ATTEMPT       2   /* SSH login attempt detected         */
#define ALERT_BRUTE_FORCE       3   /* Threshold exceeded — block IP      */
#define ALERT_SSH_AUTH_FAIL     4   /* Single SSH auth failure            */

/* ──────────────────────── Structures ──────────────────────── */

/* Alert event pushed to userspace via ring buffer */
struct ips_event {
    __u32  src_ip;          /* Source IPv4 address (network order)         */
    __u32  dst_ip;          /* Destination IPv4 address (network order)    */
    __u16  dst_port;        /* Destination port (host order)              */
    __u16  src_port;        /* Source port (host order)                   */
    __u32  pid;             /* PID of the process                        */
    __u32  fail_count;      /* Cumulative failed login count for src_ip   */
    __u64  first_seen_ns;   /* Timestamp of first failure (ktime ns)      */
    __u64  last_seen_ns;    /* Timestamp of latest failure (ktime ns)     */
    __u8   alert_type;      /* ALERT_* constant                          */
    __u8   _pad[3];
    char   comm[16];        /* Process comm name                         */
};

/* Per-IP tracking entry stored in a BPF hash map */
struct ip_track {
    __u32  fail_count;
    __u64  first_seen_ns;
    __u64  last_seen_ns;
    __u64  window_start_ns; /* Start of the current sliding window       */
};

/* IPS runtime configuration (written by userspace) */
struct ips_config {
    __u32 enabled;              /* Master kill switch                    */
    __u32 fail_threshold;       /* Failures before ALERT_BRUTE_FORCE    */
    __u64 time_window_ns;       /* Sliding window in nanoseconds        */
    __u32 monitor_all_tcp;      /* If 1, alert on every tcp_v4_connect  */
};

/* ──────────────────────── BPF Maps ──────────────────────── */

/* Ring buffer for IPS alerts → consumed by ips_agent.py */
struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 64 * 1024);  /* 64 KB — lightweight for 2W devices */
} ips_events SEC(".maps");

/* Per-IP failed login tracker */
struct {
    __uint(type, BPF_MAP_TYPE_LRU_HASH);
    __uint(max_entries, MAX_TRACKED_IPS);
    __type(key, __u32);              /* IPv4 address */
    __type(value, struct ip_track);
} failed_logins SEC(".maps");

/* Runtime configuration (single entry, index 0) */
struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 1);
    __type(key, __u32);
    __type(value, struct ips_config);
} ips_cfg SEC(".maps");

/* Temporary storage for connect args across kprobe/kretprobe */
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 4096);
    __type(key, __u64);              /* pid_tgid */
    __type(value, struct sock *);
} connect_args SEC(".maps");

/* ──────────────────────── Helpers ──────────────────────── */

static __always_inline struct ips_config *get_config(void)
{
    __u32 zero = 0;
    return bpf_map_lookup_elem(&ips_cfg, &zero);
}

static __always_inline void submit_alert(
    __u32 src_ip, __u32 dst_ip,
    __u16 src_port, __u16 dst_port,
    __u32 fail_count,
    __u64 first_ns, __u64 last_ns,
    __u8  alert_type)
{
    struct ips_event *e = bpf_ringbuf_reserve(&ips_events, sizeof(*e), 0);
    if (!e)
        return;

    e->src_ip       = src_ip;
    e->dst_ip       = dst_ip;
    e->dst_port     = dst_port;
    e->src_port     = src_port;
    e->pid          = bpf_get_current_pid_tgid() >> 32;
    e->fail_count   = fail_count;
    e->first_seen_ns = first_ns;
    e->last_seen_ns  = last_ns;
    e->alert_type   = alert_type;

    bpf_get_current_comm(&e->comm, sizeof(e->comm));

    bpf_ringbuf_submit(e, 0);
}

/* ──────────────────── tcp_v4_connect kprobe ──────────────── */
/*
 * Fires when any process initiates an IPv4 TCP connection.
 * We stash the sock pointer and resolve the address on return.
 */

SEC("kprobe/tcp_v4_connect")
int BPF_KPROBE(trace_tcp_v4_connect, struct sock *sk)
{
    struct ips_config *cfg = get_config();
    if (!cfg || !cfg->enabled)
        return 0;

    __u64 pid_tgid = bpf_get_current_pid_tgid();
    bpf_map_update_elem(&connect_args, &pid_tgid, &sk, BPF_ANY);
    return 0;
}

SEC("kretprobe/tcp_v4_connect")
int BPF_KRETPROBE(trace_tcp_v4_connect_ret, int ret)
{
    struct ips_config *cfg = get_config();
    if (!cfg || !cfg->enabled)
        return 0;

    __u64 pid_tgid = bpf_get_current_pid_tgid();
    struct sock **skp = bpf_map_lookup_elem(&connect_args, &pid_tgid);
    if (!skp) return 0;

    struct sock *sk = *skp;
    bpf_map_delete_elem(&connect_args, &pid_tgid);

    if (ret != 0)
        return 0;  /* Connection failed at kernel level */

    /* Read socket addresses */
    __u32 dst_ip  = BPF_CORE_READ(sk, __sk_common.skc_daddr);
    __u32 src_ip  = BPF_CORE_READ(sk, __sk_common.skc_rcv_saddr);
    __u16 dst_port = bpf_ntohs(BPF_CORE_READ(sk, __sk_common.skc_dport));
    __u16 src_port = BPF_CORE_READ(sk, __sk_common.skc_num);

    /* Always alert on SSH connections */
    if (dst_port == SSH_PORT || src_port == SSH_PORT) {
        __u64 now = bpf_ktime_get_ns();
        submit_alert(src_ip, dst_ip, src_port, dst_port,
                     0, now, now, ALERT_SSH_ATTEMPT);
        return 0;
    }

    /* Optionally alert on all TCP connects */
    if (cfg->monitor_all_tcp) {
        __u64 now = bpf_ktime_get_ns();
        submit_alert(src_ip, dst_ip, src_port, dst_port,
                     0, now, now, ALERT_TCP_CONNECT);
    }

    return 0;
}

/* ──────────────── SSH auth failure tracking ──────────────── */
/*
 * Strategy: We attach to the tracepoint for sched_process_exit
 * and check if the exiting process is sshd's auth child
 * (short-lived child that exits non-zero on auth failure).
 *
 * Alternatively, we hook tcp_v4_connect for SSH port AND
 * trace the accept side for inbound SSH. Below we use
 * inet_csk_accept (return probe) which catches inbound
 * TCP connections that succeed — specifically SSH on port 22.
 */

SEC("kretprobe/inet_csk_accept")
int BPF_KRETPROBE(trace_inet_csk_accept, struct sock *sk)
{
    struct ips_config *cfg = get_config();
    if (!cfg || !cfg->enabled)
        return 0;

    if (!sk)
        return 0;

    __u16 local_port = BPF_CORE_READ(sk, __sk_common.skc_num);

    /* Only interested in SSH (port 22) inbound connections */
    if (local_port != SSH_PORT)
        return 0;

    __u32 src_ip = BPF_CORE_READ(sk, __sk_common.skc_daddr);
    __u64 now    = bpf_ktime_get_ns();

    /* Look up or create tracking entry for this source IP */
    struct ip_track *track = bpf_map_lookup_elem(&failed_logins, &src_ip);

    if (!track) {
        /* First SSH connection from this IP — start tracking */
        struct ip_track new_track = {
            .fail_count     = 0,
            .first_seen_ns  = now,
            .last_seen_ns   = now,
            .window_start_ns = now,
        };
        bpf_map_update_elem(&failed_logins, &src_ip, &new_track, BPF_ANY);

        submit_alert(src_ip, 0, 0, SSH_PORT,
                     0, now, now, ALERT_SSH_ATTEMPT);
        return 0;
    }

    /* Sliding window reset */
    __u64 window_ns = cfg->time_window_ns;
    if (window_ns == 0)
        window_ns = 300ULL * 1000000000ULL;  /* Default: 5 minutes */

    if (now - track->window_start_ns > window_ns) {
        /* Window expired — reset counters */
        track->fail_count     = 0;
        track->window_start_ns = now;
        track->first_seen_ns  = now;
    }

    /* Increment failure count (we count every new SSH accept;
     * ips_agent.py correlates with auth.log for true failures) */
    track->fail_count++;
    track->last_seen_ns = now;

    bpf_map_update_elem(&failed_logins, &src_ip, track, BPF_ANY);

    /* Check threshold */
    __u32 threshold = cfg->fail_threshold;
    if (threshold == 0)
        threshold = 5;

    if (track->fail_count >= threshold) {
        /* BRUTE FORCE detected — send high-priority alert */
        submit_alert(src_ip, 0, 0, SSH_PORT,
                     track->fail_count,
                     track->first_seen_ns,
                     track->last_seen_ns,
                     ALERT_BRUTE_FORCE);

        /* Reset after alerting to avoid spamming */
        track->fail_count     = 0;
        track->window_start_ns = now;
        bpf_map_update_elem(&failed_logins, &src_ip, track, BPF_ANY);
    } else {
        /* Individual SSH auth event */
        submit_alert(src_ip, 0, 0, SSH_PORT,
                     track->fail_count,
                     track->first_seen_ns,
                     track->last_seen_ns,
                     ALERT_SSH_AUTH_FAIL);
    }

    return 0;
}

/* ────────────────────────── License ────────────────────────── */

char LICENSE[] SEC("license") = "GPL";
