#!/usr/bin/env python3
"""
OmniClaw Kernel Bridge - Python Bindings
Provides Python interface to the eBPF kernel monitor
"""

import ctypes
import json
import logging
import threading
import time
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

logger = logging.getLogger("OmniClaw.KernelBridge")


class EventType(Enum):
    SYSCALL = 0
    FILE = 1
    NETWORK = 2
    PROCESS = 3
    ERROR = 4


@dataclass
class KernelEvent:
    """Represents a kernel event"""
    type: EventType
    pid: int
    ppid: int
    uid: int
    gid: int
    timestamp: int
    syscall_nr: int
    ret: int
    comm: str
    data: str


@dataclass
class ProcessStats:
    """Process statistics"""
    pid: int
    ppid: int
    uid: int
    gid: int
    comm: str
    start_time: int
    syscall_count: int


class KernelBridgePython:
    """
    Python interface to the OmniClaw Kernel Bridge
    Monitors system calls, file operations, and network activity
    """
    
    def __init__(self, lib_path: str = None):
        """
        Initialize the kernel bridge
        
        Args:
            lib_path: Path to the compiled shared library
        """
        self.lib = None
        self.handle = None
        self.running = False
        self.event_thread = None
        self.event_callbacks: List[Callable[[KernelEvent], None]] = []
        self.event_buffer: List[KernelEvent] = []
        self.buffer_lock = threading.Lock()
        
        # Load the shared library
        if lib_path:
            self._load_library(lib_path)
        else:
            # Try default paths
            default_paths = [
                "/usr/local/omniclaw/kernel_bridge/libomniclaw_bridge.so",
                "./kernel_bridge/build/libomniclaw_bridge.so",
                "./libomniclaw_bridge.so"
            ]
            for path in default_paths:
                if Path(path).exists():
                    self._load_library(path)
                    break
        
        if not self.lib:
            logger.warning("Kernel bridge library not found, running in fallback mode")
    
    def _load_library(self, path: str):
        """Load the shared library"""
        try:
            self.lib = ctypes.CDLL(path)
            self._setup_types()
            logger.info(f"Loaded kernel bridge library from {path}")
        except Exception as e:
            logger.error(f"Failed to load library from {path}: {e}")
    
    def _setup_types(self):
        """Set up ctypes type signatures"""
        if not self.lib:
            return
        
        # Define C structures
        class CEvent(ctypes.Structure):
            _fields_ = [
                ("type", ctypes.c_uint32),
                ("pid", ctypes.c_uint32),
                ("ppid", ctypes.c_uint32),
                ("uid", ctypes.c_uint32),
                ("gid", ctypes.c_uint32),
                ("timestamp", ctypes.c_uint64),
                ("syscall_nr", ctypes.c_uint64),
                ("ret", ctypes.c_int64),
                ("comm", ctypes.c_char * 16),
                ("data", ctypes.c_char * 256)
            ]
        
        class CBridgeStats(ctypes.Structure):
            _fields_ = [
                ("process_count", ctypes.c_uint32),
                ("events_pending", ctypes.c_uint32),
                ("total_events", ctypes.c_uint64)
            ]
        
        self.CEvent = CEvent
        self.CBridgeStats = CBridgeStats
        
        # Set up function signatures
        self.lib.omniclaw_bridge_create.restype = ctypes.c_void_p
        self.lib.omniclaw_bridge_create.argtypes = []
        
        self.lib.omniclaw_bridge_destroy.restype = None
        self.lib.omniclaw_bridge_destroy.argtypes = [ctypes.c_void_p]
        
        self.lib.omniclaw_bridge_init.restype = ctypes.c_int
        self.lib.omniclaw_bridge_init.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        
        self.lib.omniclaw_bridge_start.restype = ctypes.c_int
        self.lib.omniclaw_bridge_start.argtypes = [ctypes.c_void_p]
        
        self.lib.omniclaw_bridge_stop.restype = None
        self.lib.omniclaw_bridge_stop.argtypes = [ctypes.c_void_p]
        
        self.lib.omniclaw_bridge_get_next_event.restype = ctypes.c_int
        self.lib.omniclaw_bridge_get_next_event.argtypes = [ctypes.c_void_p, ctypes.POINTER(CEvent)]
        
        self.lib.omniclaw_bridge_get_stats.restype = CBridgeStats
        self.lib.omniclaw_bridge_get_stats.argtypes = [ctypes.c_void_p]
    
    def init(self, ringbuf_size: int = 256 * 1024,
             monitor_syscalls: bool = True,
             monitor_files: bool = False,
             monitor_network: bool = False,
             monitor_all: bool = False,
             target_pid: int = 0) -> bool:
        """
        Initialize the kernel bridge
        
        Args:
            ringbuf_size: Size of the ring buffer
            monitor_syscalls: Monitor system calls
            monitor_files: Monitor file operations
            monitor_network: Monitor network activity
            monitor_all: Monitor all events
            target_pid: Specific PID to monitor (0 = all)
            
        Returns:
            True if successful
        """
        if not self.lib:
            logger.warning("Library not loaded, cannot initialize kernel bridge")
            return False
        
        self.handle = self.lib.omniclaw_bridge_create()
        if not self.handle:
            logger.error("Failed to create bridge handle")
            return False
        
        # Build config structure
        class CConfig(ctypes.Structure):
            _fields_ = [
                ("ringbuf_size", ctypes.c_uint32),
                ("monitor_syscalls", ctypes.c_bool),
                ("monitor_files", ctypes.c_bool),
                ("monitor_network", ctypes.c_bool),
                ("monitor_all", ctypes.c_bool),
                ("target_pid", ctypes.c_uint32)
            ]
        
        config = CConfig(
            ringbuf_size=ringbuf_size,
            monitor_syscalls=monitor_syscalls,
            monitor_files=monitor_files,
            monitor_network=monitor_network,
            monitor_all=monitor_all,
            target_pid=target_pid
        )
        
        result = self.lib.omniclaw_bridge_init(self.handle, ctypes.byref(config))
        if result != 0:
            logger.error(f"Failed to initialize bridge: {result}")
            self.lib.omniclaw_bridge_destroy(self.handle)
            self.handle = None
            return False
        
        logger.info("Kernel bridge initialized successfully")
        return True
    
    def start(self) -> bool:
        """Start monitoring (non-blocking)"""
        if not self.handle:
            logger.error("Bridge not initialized")
            return False
        
        self.running = True
        
        # Start event polling thread
        self.event_thread = threading.Thread(target=self._event_loop)
        self.event_thread.daemon = True
        self.event_thread.start()
        
        logger.info("Kernel bridge monitoring started")
        return True
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
        
        if self.event_thread:
            self.event_thread.join(timeout=2)
        
        if self.handle and self.lib:
            self.lib.omniclaw_bridge_stop(self.handle)
        
        logger.info("Kernel bridge stopped")
    
    def _event_loop(self):
        """Background thread for polling events"""
        while self.running:
            if not self.handle or not self.lib:
                time.sleep(0.1)
                continue
            
            event = self.CEvent()
            result = self.lib.omniclaw_bridge_get_next_event(
                self.handle, 
                ctypes.byref(event)
            )
            
            if result == 0:
                # Convert to Python event
                py_event = self._convert_event(event)
                
                # Add to buffer
                with self.buffer_lock:
                    self.event_buffer.append(py_event)
                    if len(self.event_buffer) > 10000:
                        self.event_buffer.pop(0)
                
                # Notify callbacks
                for callback in self.event_callbacks:
                    try:
                        callback(py_event)
                    except Exception as e:
                        logger.error(f"Event callback error: {e}")
            else:
                # No events available
                time.sleep(0.01)
    
    def _convert_event(self, c_event) -> KernelEvent:
        """Convert C event to Python event"""
        return KernelEvent(
            type=EventType(c_event.type),
            pid=c_event.pid,
            ppid=c_event.ppid,
            uid=c_event.uid,
            gid=c_event.gid,
            timestamp=c_event.timestamp,
            syscall_nr=c_event.syscall_nr,
            ret=c_event.ret,
            comm=c_event.comm.decode('utf-8', errors='ignore').strip('\x00'),
            data=c_event.data.decode('utf-8', errors='ignore').strip('\x00')
        )
    
    def add_event_callback(self, callback: Callable[[KernelEvent], None]):
        """Add an event callback"""
        self.event_callbacks.append(callback)
    
    def remove_event_callback(self, callback: Callable[[KernelEvent], None]):
        """Remove an event callback"""
        if callback in self.event_callbacks:
            self.event_callbacks.remove(callback)
    
    def get_events(self, max_events: int = 100) -> List[KernelEvent]:
        """Get buffered events"""
        with self.buffer_lock:
            events = self.event_buffer[-max_events:]
            self.event_buffer = self.event_buffer[:-max_events]
            return events
    
    def get_stats(self) -> Dict[str, Any]:
        """Get bridge statistics"""
        if not self.handle or not self.lib:
            return {"error": "Not initialized"}
        
        stats = self.lib.omniclaw_bridge_get_stats(self.handle)
        return {
            "process_count": stats.process_count,
            "events_pending": stats.events_pending,
            "total_events": stats.total_events
        }
    
    def cleanup(self):
        """Clean up resources"""
        self.stop()
        
        if self.handle and self.lib:
            self.lib.omniclaw_bridge_destroy(self.handle)
            self.handle = None
        
        logger.info("Kernel bridge cleaned up")


# Fallback monitor using /proc and psutil
class FallbackMonitor:
    """Fallback system monitor when eBPF is not available"""
    
    def __init__(self):
        self.running = False
        self.monitor_thread = None
        self.process_stats: Dict[int, Dict] = {}
        self.callbacks: List[Callable] = []
        
        try:
            import psutil
            self.psutil = psutil
        except ImportError:
            self.psutil = None
            logger.warning("psutil not available, fallback monitoring limited")
    
    def start(self):
        """Start fallback monitoring"""
        if not self.psutil:
            return False
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        logger.info("Fallback monitoring started")
        return True
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
    
    def _monitor_loop(self):
        """Monitor loop using psutil"""
        while self.running:
            try:
                # Collect process stats
                for proc in self.psutil.process_iter(['pid', 'ppid', 'name', 'cpu_percent', 'memory_percent']):
                    try:
                        pinfo = proc.info
                        self.process_stats[pinfo['pid']] = {
                            'pid': pinfo['pid'],
                            'ppid': pinfo['ppid'],
                            'name': pinfo['name'],
                            'cpu': pinfo['cpu_percent'],
                            'memory': pinfo['memory_percent'],
                            'timestamp': time.time()
                        }
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                # Clean up old entries
                current_time = time.time()
                self.process_stats = {
                    k: v for k, v in self.process_stats.items()
                    if current_time - v['timestamp'] < 60
                }
                
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Fallback monitor error: {e}")
                time.sleep(5)
    
    def get_process_stats(self) -> Dict[int, Dict]:
        """Get current process statistics"""
        return self.process_stats.copy()


# Main interface
class SystemMonitor:
    """Main system monitoring interface"""
    
    def __init__(self):
        self.bridge = KernelBridgePython()
        self.fallback = FallbackMonitor()
        self.active_monitor = None
    
    def init(self, **kwargs) -> bool:
        """Initialize monitoring"""
        if self.bridge.init(**kwargs):
            self.active_monitor = self.bridge
            return True
        else:
            logger.info("Using fallback monitor")
            self.active_monitor = self.fallback
            return self.fallback.start()
    
    def start(self) -> bool:
        """Start monitoring"""
        if self.active_monitor == self.bridge:
            return self.bridge.start()
        return True
    
    def stop(self):
        """Stop monitoring"""
        if self.active_monitor:
            self.active_monitor.stop()
    
    def get_events(self, max_events: int = 100) -> List[KernelEvent]:
        """Get events"""
        if self.active_monitor == self.bridge:
            return self.bridge.get_events(max_events)
        return []
    
    def get_process_stats(self) -> Dict:
        """Get process statistics"""
        if self.active_monitor == self.bridge:
            return self.bridge.get_stats()
        elif self.active_monitor == self.fallback:
            return self.fallback.get_process_stats()
        return {}
    
    def add_event_callback(self, callback: Callable):
        """Add event callback"""
        if self.active_monitor == self.bridge:
            self.bridge.add_event_callback(callback)
        else:
            self.fallback.callbacks.append(callback)
