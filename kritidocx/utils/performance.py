"""
PERFORMANCE MONITORING MODULE (The Stopwatch & Profiler)
--------------------------------------------------------
Responsibility:
Track execution time, CPU usage, and Memory consumption for pipeline steps.

Key Features:
1. ⏱️ Unified Timer: Works as both a `Context Manager` (`with Timer:`) AND a `Decorator` (`@Timer`).
2. 💾 Memory Delta: Tracks how much RAM was consumed/released during a block.
3. 📊 Final Report: Accumulates metrics to print a "Top Slowest Functions" summary at the end.
4. 🚨 Slow Warning: Warns if a specific operation exceeds a defined threshold (e.g. > 1 sec).

Usage:
    # 1. As Context Manager
    with Timer("Parsing HTML"):
        parser.run()

    # 2. As Decorator
    @Timer(name="Heavy Calculation", warn_threshold_ms=500)
    def calculate(): ...

    # 3. Get Report
    PerformanceMonitor.print_summary()
"""

import time
import functools
import os
import psutil  # Requires 'psutil' (Added for RAM checks)
import statistics
from collections import defaultdict

# Internal Import
from kritidocx.utils.logger import logger, Colors

# Check environment for explicit profiling flag
ENABLE_PROFILING = True  # In prod settings this could come from AppConfig

class PerformanceRegistry:
    """
    Central storage for performance metrics.
    Singleton pattern implicit via module usage.
    """
    _records = defaultdict(list) # Stores list of durations per key
    _start_time = None

    @classmethod
    def start_session(cls):
        """Called when pipeline starts."""
        cls._records.clear()
        cls._start_time = time.perf_counter()

    @classmethod
    def record(cls, name, duration_ms, memory_delta_mb):
        """Store a single execution metric."""
        cls._records[name].append({
            'time': duration_ms,
            'memory': memory_delta_mb
        })

    @classmethod
    def get_summary(cls):
        """Calculates average/max stats."""
        stats = []
        for name, data in cls._records.items():
            times = [d['time'] for d in data]
            total_mem = sum([d['memory'] for d in data])
            
            stats.append({
                'name': name,
                'count': len(times),
                'total_time': sum(times),
                'avg_time': statistics.mean(times) if times else 0,
                'max_time': max(times) if times else 0,
                'net_memory': total_mem
            })
        
        # Sort by Total Time desc
        return sorted(stats, key=lambda x: x['total_time'], reverse=True)

    @classmethod
    def print_report(cls):
        """
        Prints a beautiful ASCII table of performance metrics.
        """
        summary = cls.get_summary()
        if not summary: return

        # ASCII Table Formatting
        logger.debug(f"\n{Colors.BOLD}{Colors.CYAN}" + "="*70)
        logger.debug(f" 🏎️  PERFORMANCE SUMMARY REPORT")
        logger.debug("="*70)
        logger.debug(f" {'OPERATION':<30} | {'CALLS':<5} | {'AVG (ms)':<9} | {'TOTAL (s)':<9} | {'RAM (MB)':<8}")
        logger.debug("-" * 70 + f"{Colors.RESET}")

        total_app_time = 0
        
        for item in summary:
            # Color logic for slow items
            row_color = Colors.RESET
            if item['avg_time'] > 500: row_color = Colors.YELLOW # Warn
            if item['avg_time'] > 1500: row_color = Colors.RED   # Critical

            total_app_time += item['total_time']
            
            logger.debug(f"{row_color} {item['name']:<30} | {item['count']:<5} | {item['avg_time']:<9.2f} | {item['total_time']/1000:<9.4f} | {item['net_memory']:<+8.2f}{Colors.RESET}")

        total_wall = time.perf_counter() - cls._start_time
        logger.debug(f"{Colors.BOLD}" + "-"*70)
        logger.debug(f" ⏱️  Execution: {total_app_time/1000:.3f}s (Tracked) / {total_wall:.3f}s (Wall Clock)")
        logger.debug(f" 💾  Peak RSS: {cls._get_current_memory():.2f} MB")
        logger.debug("="*70 + f"{Colors.RESET}\n")

    @staticmethod
    def _get_current_memory():
        """Returns current Process RAM usage in MB."""
        try:
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 * 1024)
        except ImportError:
            return 0.0

class Timer:
    """
    Hybrid Timer: Supports both Decorator and Context Manager.
    Captures RAM Delta and Time Delta.
    """

    def __init__(self, name="Op", warn_threshold_ms=None):
        self.name = name
        self.warn_ms = warn_threshold_ms
        self.start_time = 0
        self.start_mem = 0

    def _measure_mem(self):
        """Helper to get current MB safely."""
        return PerformanceRegistry._get_current_memory()

    # --- CONTEXT MANAGER ---
    def __enter__(self):
        self.start_time = time.perf_counter()
        if ENABLE_PROFILING:
            self.start_mem = self._measure_mem()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        end_time = time.perf_counter()
        end_mem = self._measure_mem() if ENABLE_PROFILING else 0
        
        duration_ms = (end_time - self.start_time) * 1000
        mem_delta = end_mem - self.start_mem

        # 1. Log completion (Visual feedback)
        # Indent visually via Logger hierarchy if possible, or just raw
        # (Assuming Logger is smart enough)
        
        # Color Coding based on threshold
        color = Colors.GREY
        note = ""
        
        if self.warn_ms and duration_ms > self.warn_ms:
            color = Colors.YELLOW
            note = f" [SLOW > {self.warn_ms}ms]"
            
        logger.debug(f"{color}⏱ {self.name} took {duration_ms:.2f}ms{note}{Colors.RESET}")

        # 2. Register metric
        PerformanceRegistry.record(self.name, duration_ms, mem_delta)

    # --- DECORATOR ---
    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Same logic as Context Manager
            # Determine better name if default used
            log_name = self.name if self.name != "Op" else func.__name__
            
            with Timer(log_name, self.warn_ms):
                return func(*args, **kwargs)
        return wrapper

# =========================================================================
# 🧮 HELPERS (Lightweight Tools)
# =========================================================================

class MemoryWatch:
    """
    Strict monitor for memory leaks in a block.
    Forces Garbage Collection before measurement to be precise.
    """
    def __init__(self, tag):
        self.tag = tag
        self.before = 0

    def __enter__(self):
        import gc
        gc.collect() # Force cleanup before measuring
        self.before = PerformanceRegistry._get_current_memory()
        logger.debug(f"💾 MemWatch Start [{self.tag}]: {self.before:.2f} MB")

    def __exit__(self, *args):
        import gc
        after = PerformanceRegistry._get_current_memory()
        diff = after - self.before
        
        level = "OK"
        if diff > 10: level = "HIGH" 
        if diff > 50: level = "CRITICAL LEAK?"

        log_fn = logger.warning if diff > 50 else logger.debug
        log_fn(f"💾 MemWatch End   [{self.tag}]: {after:.2f} MB (Delta: {diff:+.2f} MB) [{level}]")

# =========================================================================
# 🏁 BOOTSTRAP (For testing logic standalone)
# =========================================================================
# This starts the clock immediately upon module load
PerformanceRegistry.start_session()