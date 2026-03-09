"""
UTILS PACKAGE (The Toolkit)
---------------------------
Common shared resources for Logging, File I/O, and Performance Monitoring.

This package exposes a flattened API for ease of use across the Engine.
It also manages the 'System Teardown' process (Cleanup & Reporting).

Components:
    - Logger: Intelligent console/file logging & visual hierarchy.
    - FileManager: Safe IO, Temp file tracking & Sanitization.
    - Timer/Performance: Execution profiling & RAM monitoring.

Usage:
    from kritidocx.utils import logger, FileManager, Timer
"""

# =========================================================================
# 📦 IMPORT MODULES (Flatten Namespace)
# =========================================================================

# 1. Logger System (Singleton)
# We export 'logger' instance directly, not the class, to enforce Singleton usage.
from .logger import logger, Colors

# 2. File Operations
from .file_manager import FileManager

# 3. Performance & Profiling
from .performance import Timer, PerformanceRegistry, MemoryWatch

# =========================================================================
# 🔄 GLOBAL SYSTEM HOOKS (Lifecycle Management)
# =========================================================================

def bootstrap_utils():
    """
    Optional initialization hook. 
    Currently, sub-modules self-initialize (Performance Registry etc),
    but this placeholder exists if explicit startup logic is needed later.
    """
    logger.debug("Utils package bootstrap checks passed.")

def teardown_system():
    """
    [MASTER SHUTDOWN]
    This function should be called at the very end of the Pipeline execution.
    It acts as the Garbage Collector and Analyst.
    
    Actions:
    1. 🧹 Disk Cleanup: Deletes all temporary files (images/json/downloads) generated during run.
    2. 🏎️ Profiling: Generates the 'Performance Summary' table in the console.
    3. 🏁 Logging: Signals the final exit.
    
    Usage:
        try:
            pipeline.run()
        finally:
            from kritidocx.utils import teardown_system
            teardown_system()
    """
    # Separator line for visual clarity
    logger.debug("\n" + (Colors.DIM + "-"*70 + Colors.RESET))
    
    # 1. Performance Report
    logger.info("Generating Final Performance Metrics...")
    PerformanceRegistry.print_report()
    
    # 2. Temp File Cleanup
    # Using FileManager's registry to delete everything tracked
    logger.info("Executing Cleanup Procedures...")
    FileManager.clean_all_temp_files()
    
    # 3. Goodbye
    logger.info(f"System Teardown Complete. All threads closed.")

# =========================================================================
# 🔒 PUBLIC API EXPORT
# =========================================================================
# 'from kritidocx.utils import *' will import ONLY these
__all__ = [
    # Logger
    'logger', 
    'Colors',
    
    # File Handler
    'FileManager',
    
    # Profiler
    'Timer', 
    'PerformanceRegistry', 
    'MemoryWatch',
    
    # System Functions
    'teardown_system'
]