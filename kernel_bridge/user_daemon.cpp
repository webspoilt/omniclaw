#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <signal.h>
#include <unistd.h>
#include <zmq.hpp>
#include <bpf/libbpf.h>

struct forensic_event {
    uint32_t pid;
    uint64_t pc;
    uint64_t sp;
    char comm[16];
    uint8_t memory_snippet[64];
};

void send_zmq_alert(zmq::socket_t& socket, uint32_t pid, const std::string& type) {
    // We send a JSON or msgpack formatted string over a DEALER socket
    std::string payload = R"({"header": {"type": "ANOMALY_ALERT", "routing_id": "ebpf_daemon"}, "payload": {"pid": )" + std::to_string(pid) + R"(, "event": ")" + type + R"("}})";
    zmq::message_t request(payload.size());
    memcpy(request.data(), payload.data(), payload.size());
    socket.send(request, zmq::send_flags::none);
}

void freeze_cgroup(uint32_t pid) {
    std::string cg_path = "/sys/fs/cgroup/omniclaw/" + std::to_string(pid) + "/cgroup.freeze";
    std::ofstream cg_file(cg_path);
    if(cg_file.is_open()) {
        cg_file << "1";
        cg_file.close();
        std::cout << "[eBPF Daemon] Froze cgroup for PID " << pid << std::endl;
    }
}

int handle_event(void *ctx, void *data, size_t data_sz) {
    const struct forensic_event *e = (const struct forensic_event *)data;
    zmq::socket_t* zmq_sock = static_cast<zmq::socket_t*>(ctx);

    std::cout << "[eBPF Daemon] Intercepted exit for PID " << e->pid << " (" << e->comm << ")" << std::endl;

    // 1. Freeze cgroup
    freeze_cgroup(e->pid);
    
    // 2. Package forensics (dummy writing for now)
    std::string vault_path = "/var/lib/omniclaw/forensics/pid_" + std::to_string(e->pid) + ".vault";
    std::ofstream vault_file(vault_path, std::ios::binary);
    if(vault_file.is_open()) {
        vault_file.write(reinterpret_cast<const char*>(e->memory_snippet), sizeof(e->memory_snippet));
        vault_file.close();
    }
    
    // 3. Send ZMQ ANOMALY_ALERT to Orchestrator
    send_zmq_alert(*zmq_sock, e->pid, "CRITICAL_EXIT_INTERCEPTED");

    // 4. Kill PID securely
    kill(e->pid, SIGKILL);
    
    return 0;
}

int main(int argc, char **argv) {
    zmq::context_t ctx(1);
    zmq::socket_t sock(ctx, zmq::socket_type::dealer);
    sock.connect("tcp://127.0.0.0:5555");
    
    std::cout << "[eBPF Daemon] Started and connected to ZMQ Orchestrator." << std::endl;

    // TODO: Setup libbpf ring buffer polling here.
    // struct ring_buffer *rb = ring_buffer__new(bpf_map__fd(forensics_rb), handle_event, &sock, NULL);
    // while (true) { ring_buffer__poll(rb, 100); }
    
    return 0;
}
