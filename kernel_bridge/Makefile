# OmniClaw Kernel Bridge Makefile
# Builds eBPF programs and userspace components

CC = clang
CXX = g++
CFLAGS = -O2 -g -Wall -Wextra
BPF_CFLAGS = -target bpf -D__TARGET_ARCH_x86_64 -I/usr/include/x86_64-linux-gnu
CXXFLAGS = -std=c++17 -O2 -g -Wall -Wextra
LDFLAGS = -lbpf -lelf -lz

# Directories
SRC_DIR = src
BUILD_DIR = build
INSTALL_DIR = /usr/local/omniclaw/kernel_bridge

# Source files
BPF_SRCS = $(wildcard $(SRC_DIR)/bpf/*.c)
BPF_OBJS = $(patsubst $(SRC_DIR)/bpf/%.c,$(BUILD_DIR)/%.bpf.o,$(BPF_SRCS))

CPP_SRCS = $(wildcard $(SRC_DIR)/cpp/*.cpp)
CPP_OBJS = $(patsubst $(SRC_DIR)/cpp/%.cpp,$(BUILD_DIR)/%.o,$(CPP_SRCS))

# Targets
.PHONY: all clean install uninstall ips

all: $(BUILD_DIR) $(BPF_OBJS) $(BUILD_DIR)/omniclaw_bridge

# Build only the IPS eBPF monitor
ips: $(BUILD_DIR) $(BUILD_DIR)/monitor.bpf.o

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

# Compile eBPF programs (CO-RE object files)
$(BUILD_DIR)/%.bpf.o: $(SRC_DIR)/bpf/%.c
	$(CC) $(CFLAGS) $(BPF_CFLAGS) -c $< -o $@

# Compile C++ userspace components
$(BUILD_DIR)/%.o: $(SRC_DIR)/cpp/%.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

# Link userspace bridge
$(BUILD_DIR)/omniclaw_bridge: $(CPP_OBJS)
	$(CXX) $(CXXFLAGS) $^ -o $@ $(LDFLAGS)

install: all
	install -d $(INSTALL_DIR)
	install -m 755 $(BUILD_DIR)/omniclaw_bridge $(INSTALL_DIR)/
	install -m 644 $(BPF_OBJS) $(INSTALL_DIR)/
	install -m 644 $(SRC_DIR)/cpp/omniclaw_bridge.h /usr/local/include/

uninstall:
	rm -rf $(INSTALL_DIR)
	rm -f /usr/local/include/omniclaw_bridge.h

clean:
	rm -rf $(BUILD_DIR)
