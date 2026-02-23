/*
 * OmniClaw Kernel Bridge - Userspace Component
 * Interfaces with eBPF programs and provides data to Python
 */

#include "omniclaw_bridge.h"
#include <iostream>
#include <cstring>
#include <unistd.h>
#include <signal.h>
#include <fcntl.h>
#include <sys/resource.h>
#include <bpf/libbpf.h>
#include <bpf/bpf.h>

namespace omniclaw {

// Global instance for signal handling
KernelBridge* g_bridge = nullptr;

void signal_handler(int sig) {
    if (g_bridge) {
        std::cerr << "\nReceived signal " << sig << ", shutting down..." << std::endl;
        g_bridge->stop();
    }
}

KernelBridge::KernelBridge() 
    : running_(false)
    , skel_(nullptr)
    , ringbuf_(nullptr)
    , event_callback_(nullptr)
    , callback_data_(nullptr) {
    
    // Set up signal handlers
    g_bridge = this;
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);
    
    // Bump RLIMIT_MEMLOCK for eBPF
    struct rlimit rlim = {
        .rlim_cur = RLIM_INFINITY,
        .rlim_max = RLIM_INFINITY,
    };
    setrlimit(RLIMIT_MEMLOCK, &rlim);
}

KernelBridge::~KernelBridge() {
    cleanup();
    g_bridge = nullptr;
}

int KernelBridge::init(const BridgeConfig& config) {
    config_ = config;
    
    std::cout << "Initializing OmniClaw Kernel Bridge..." << std::endl;
    
    // Open and load BPF skeleton
    skel_ = syscall_monitor_bpf__open();
    if (!skel_) {
        std::cerr << "Failed to open BPF skeleton" << std::endl;
        return -1;
    }
    
    // Set up ring buffer map
    bpf_map__set_max_entries(skel_->maps.events, config.ringbuf_size);
    
    // Load and verify BPF programs
    int err = syscall_monitor_bpf__load(skel_);
    if (err) {
        std::cerr << "Failed to load BPF skeleton: " << err << std::endl;
        cleanup();
        return err;
    }
    
    // Set configuration
    uint32_t zero = 0;
    struct {
        uint32_t monitor_all;
        uint32_t monitor_syscalls;
        uint32_t monitor_files;
        uint32_t monitor_network;
        uint32_t target_pid;
    } cfg = {
        .monitor_all = config.monitor_all ? 1u : 0u,
        .monitor_syscalls = config.monitor_syscalls ? 1u : 0u,
        .monitor_files = config.monitor_files ? 1u : 0u,
        .monitor_network = config.monitor_network ? 1u : 0u,
        .target_pid = config.target_pid
    };
    
    bpf_map__update_elem(skel_->maps.config, &zero, sizeof(zero),
                         &cfg, sizeof(cfg), BPF_ANY);
    
    // Attach BPF programs
    err = syscall_monitor_bpf__attach(skel_);
    if (err) {
        std::cerr << "Failed to attach BPF programs: " << err << std::endl;
        cleanup();
        return err;
    }
    
    // Set up ring buffer
    ringbuf_ = ring_buffer__new(bpf_map__fd(skel_->maps.events),
                                handle_ring_event, this, nullptr);
    if (!ringbuf_) {
        std::cerr << "Failed to create ring buffer" << std::endl;
        cleanup();
        return -1;
    }
    
    std::cout << "Kernel Bridge initialized successfully" << std::endl;
    return 0;
}

void KernelBridge::cleanup() {
    if (ringbuf_) {
        ring_buffer__free(ringbuf_);
        ringbuf_ = nullptr;
    }
    
    if (skel_) {
        syscall_monitor_bpf__destroy(skel_);
        skel_ = nullptr;
    }
}

int KernelBridge::start() {
    if (!ringbuf_) {
        std::cerr << "Bridge not initialized" << std::endl;
        return -1;
    }
    
    running_ = true;
    std::cout << "Kernel Bridge started, monitoring events..." << std::endl;
    
    while (running_) {
        // Poll ring buffer with 100ms timeout
        int err = ring_buffer__poll(ringbuf_, 100);
        if (err < 0 && err != -EINTR) {
            std::cerr << "Error polling ring buffer: " << err << std::endl;
            break;
        }
    }
    
    return 0;
}

void KernelBridge::stop() {
    running_ = false;
}

int KernelBridge::handle_ring_event(void* ctx, void* data, size_t size) {
    KernelBridge* bridge = static_cast<KernelBridge*>(ctx);
    
    if (size < sizeof(Event)) {
        std::cerr << "Event too small: " << size << std::endl;
        return 0;
    }
    
    Event* event = static_cast<Event*>(data);
    
    // Call user callback if set
    if (bridge->event_callback_) {
        bridge->event_callback_(event, bridge->callback_data_);
    }
    
    // Also add to event queue for polling
    std::lock_guard<std::mutex> lock(bridge->event_mutex_);
    bridge->event_queue_.push(*event);
    
    // Limit queue size
    while (bridge->event_queue_.size() > 10000) {
        bridge->event_queue_.pop();
    }
    
    return 0;
}

void KernelBridge::setEventCallback(EventCallback callback, void* user_data) {
    event_callback_ = callback;
    callback_data_ = user_data;
}

bool KernelBridge::getNextEvent(Event& event) {
    std::lock_guard<std::mutex> lock(event_mutex_);
    
    if (event_queue_.empty()) {
        return false;
    }
    
    event = event_queue_.front();
    event_queue_.pop();
    return true;
}

std::vector<Event> KernelBridge::getEvents(size_t max_events) {
    std::lock_guard<std::mutex> lock(event_mutex_);
    
    std::vector<Event> events;
    size_t count = std::min(max_events, event_queue_.size());
    
    for (size_t i = 0; i < count; i++) {
        events.push_back(event_queue_.front());
        event_queue_.pop();
    }
    
    return events;
}

ProcessStats KernelBridge::getProcessStats(uint32_t pid) {
    ProcessStats stats = {};
    
    if (!skel_) {
        return stats;
    }
    
    // Get process info
    struct process_info info;
    if (bpf_map__lookup_elem(skel_->maps.processes, &pid, sizeof(pid),
                             &info, sizeof(info), 0) == 0) {
        stats.pid = info.pid;
        stats.ppid = info.ppid;
        stats.uid = info.uid;
        stats.gid = info.gid;
        stats.start_time = info.start_time;
        memcpy(stats.comm, info.comm, sizeof(stats.comm));
    }
    
    // Get syscall count
    uint64_t count;
    if (bpf_map__lookup_elem(skel_->maps.syscall_counts, &pid, sizeof(pid),
                             &count, sizeof(count), 0) == 0) {
        stats.syscall_count = count;
    }
    
    return stats;
}

std::vector<ProcessStats> KernelBridge::getAllProcessStats() {
    std::vector<ProcessStats> all_stats;
    
    if (!skel_) {
        return all_stats;
    }
    
    // Iterate through process map
    uint32_t key, next_key;
    int err = bpf_map__get_next_key(skel_->maps.processes, nullptr, &key, sizeof(key));
    
    while (err == 0) {
        ProcessStats stats = getProcessStats(key);
        if (stats.pid != 0) {
            all_stats.push_back(stats);
        }
        
        next_key = key;
        err = bpf_map__get_next_key(skel_->maps.processes, &next_key, &key, sizeof(key));
    }
    
    return all_stats;
}

void KernelBridge::setMonitoringConfig(bool syscalls, bool files, bool network, bool all) {
    if (!skel_) {
        return;
    }
    
    uint32_t zero = 0;
    struct {
        uint32_t monitor_all;
        uint32_t monitor_syscalls;
        uint32_t monitor_files;
        uint32_t monitor_network;
        uint32_t target_pid;
    } cfg;
    
    bpf_map__lookup_elem(skel_->maps.config, &zero, sizeof(zero), &cfg, sizeof(cfg), 0);
    
    cfg.monitor_syscalls = syscalls ? 1u : 0u;
    cfg.monitor_files = files ? 1u : 0u;
    cfg.monitor_network = network ? 1u : 0u;
    cfg.monitor_all = all ? 1u : 0u;
    
    bpf_map__update_elem(skel_->maps.config, &zero, sizeof(zero), &cfg, sizeof(cfg), BPF_ANY);
}

BridgeStats KernelBridge::getStats() {
    BridgeStats stats = {};
    
    if (!skel_) {
        return stats;
    }
    
    // Count processes
    uint32_t key, next_key;
    int err = bpf_map__get_next_key(skel_->maps.processes, nullptr, &key, sizeof(key));
    while (err == 0) {
        stats.process_count++;
        next_key = key;
        err = bpf_map__get_next_key(skel_->maps.processes, &next_key, &key, sizeof(key));
    }
    
    // Get ring buffer stats
    stats.events_pending = event_queue_.size();
    
    return stats;
}

} // namespace omniclaw
