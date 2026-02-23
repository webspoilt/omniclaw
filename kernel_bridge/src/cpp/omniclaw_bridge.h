/*
 * OmniClaw Kernel Bridge - Header File
 * C++ API for kernel monitoring
 */

#ifndef OMNICLAW_BRIDGE_H
#define OMNICLAW_BRIDGE_H

#include <cstdint>
#include <cstddef>
#include <string>
#include <vector>
#include <queue>
#include <mutex>
#include <functional>

// Forward declarations for BPF skeleton
struct syscall_monitor_bpf;
struct ring_buffer;

namespace omniclaw {

// Event types (must match eBPF program)
enum class EventType : uint32_t {
    SYSCALL = 0,
    FILE = 1,
    NETWORK = 2,
    PROCESS = 3,
    ERROR = 4
};

// Event structure (must match eBPF program)
#pragma pack(push, 1)
struct Event {
    uint32_t type;
    uint32_t pid;
    uint32_t ppid;
    uint32_t uid;
    uint32_t gid;
    uint64_t timestamp;
    uint64_t syscall_nr;
    int64_t ret;
    char comm[16];
    char data[256];
};
#pragma pack(pop)

// Process statistics
struct ProcessStats {
    uint32_t pid;
    uint32_t ppid;
    uint32_t uid;
    uint32_t gid;
    char comm[16];
    uint64_t start_time;
    uint64_t syscall_count;
};

// Bridge statistics
struct BridgeStats {
    uint32_t process_count;
    uint32_t events_pending;
    uint64_t total_events;
};

// Configuration
struct BridgeConfig {
    uint32_t ringbuf_size = 256 * 1024;
    bool monitor_syscalls = true;
    bool monitor_files = false;
    bool monitor_network = false;
    bool monitor_all = false;
    uint32_t target_pid = 0;  // 0 = monitor all
};

// Event callback type
typedef void (*EventCallback)(const Event* event, void* user_data);

class KernelBridge {
public:
    KernelBridge();
    ~KernelBridge();
    
    // Initialize the bridge
    int init(const BridgeConfig& config);
    
    // Start monitoring (blocking)
    int start();
    
    // Stop monitoring
    void stop();
    
    // Set event callback
    void setEventCallback(EventCallback callback, void* user_data);
    
    // Get next event (non-blocking)
    bool getNextEvent(Event& event);
    
    // Get multiple events
    std::vector<Event> getEvents(size_t max_events = 100);
    
    // Get process statistics
    ProcessStats getProcessStats(uint32_t pid);
    std::vector<ProcessStats> getAllProcessStats();
    
    // Update monitoring configuration
    void setMonitoringConfig(bool syscalls, bool files, bool network, bool all);
    
    // Get bridge statistics
    BridgeStats getStats();
    
    // Check if running
    bool isRunning() const { return running_; }

private:
    void cleanup();
    static int handle_ring_event(void* ctx, void* data, size_t size);
    
    bool running_;
    BridgeConfig config_;
    
    // BPF objects
    syscall_monitor_bpf* skel_;
    ring_buffer* ringbuf_;
    
    // Event handling
    EventCallback event_callback_;
    void* callback_data_;
    std::queue<Event> event_queue_;
    std::mutex event_mutex_;
};

} // namespace omniclaw

// C API for Python bindings
extern "C" {
    typedef void* OmniclawBridgeHandle;
    typedef void (*OmniclawEventCallback)(const omniclaw::Event* event, void* user_data);
    
    OmniclawBridgeHandle omniclaw_bridge_create();
    void omniclaw_bridge_destroy(OmniclawBridgeHandle handle);
    int omniclaw_bridge_init(OmniclawBridgeHandle handle, const omniclaw::BridgeConfig* config);
    int omniclaw_bridge_start(OmniclawBridgeHandle handle);
    void omniclaw_bridge_stop(OmniclawBridgeHandle handle);
    void omniclaw_bridge_set_callback(OmniclawBridgeHandle handle, 
                                       OmniclawEventCallback callback, 
                                       void* user_data);
    int omniclaw_bridge_get_next_event(OmniclawBridgeHandle handle, omniclaw::Event* event);
    omniclaw::BridgeStats omniclaw_bridge_get_stats(OmniclawBridgeHandle handle);
}

#endif // OMNICLAW_BRIDGE_H
