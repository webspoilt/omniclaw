// modules/security/honeypot.cpp — eBPF XDP SSH brute-force detector
// Inspects TCP packets to port 22, counts per-IP attempts in LRU map.
// When threshold exceeded, marks packet for userspace TPROXY redirection
// to the shadow shell on port 2222.
//
// Build: clang -O2 -target bpf -c honeypot.cpp -o honeypot.bpf.o
// Load:  ip link set dev eth0 xdp obj honeypot.bpf.o sec xdp

#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

// LRU map: src_ip -> attempt count
struct {
    __uint(type, BPF_MAP_TYPE_LRU_HASH);
    __uint(max_entries, 1024);
    __type(key, __u32);
    __type(value, __u32);
} attack_map SEC(".maps");

#define SHADOW_PORT 2222
#define THRESHOLD   5

SEC("xdp")
int xdp_ssh_redirect(struct xdp_md *ctx) {
    void *data_end = (void *)(long)ctx->data_end;
    void *data     = (void *)(long)ctx->data;

    // -- Ethernet --
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return XDP_PASS;
    if (bpf_ntohs(eth->h_proto) != ETH_P_IP)
        return XDP_PASS;

    // -- IPv4 --
    struct iphdr *ip = data + sizeof(*eth);
    if ((void *)(ip + 1) > data_end)
        return XDP_PASS;
    if (ip->protocol != IPPROTO_TCP)
        return XDP_PASS;

    // -- TCP --
    struct tcphdr *tcp = (void *)ip + (ip->ihl * 4);
    if ((void *)(tcp + 1) > data_end)
        return XDP_PASS;

    // Only SSH (port 22)
    if (bpf_ntohs(tcp->dest) != 22)
        return XDP_PASS;

    __u32 src_ip = ip->saddr;
    __u32 *count = bpf_map_lookup_elem(&attack_map, &src_ip);
    if (count) {
        __sync_fetch_and_add(count, 1);
        if (*count > THRESHOLD) {
            // Packet is from a repeat offender.
            // Userspace iptables_helper.py reads attack_map via bpftool
            // and inserts TPROXY rules to redirect to shadow shell port 2222.
            // XDP cannot do TPROXY directly, but we let it pass so the
            // TPROXY rule in the mangle table handles redirection.
        }
    } else {
        __u32 init = 1;
        bpf_map_update_elem(&attack_map, &src_ip, &init, BPF_ANY);
    }

    return XDP_PASS;
}

char _license[] SEC("license") = "GPL";
