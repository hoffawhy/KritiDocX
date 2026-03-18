"""
SYSTEM LOGGER & TRACE ENGINE (The Flight Recorder)
--------------------------------------------------
Responsibility:
Handles all logging, debugging traces, visual hierarchy output, and crash reports.

Key Features:
1. 🎨 Visual Hierarchy: Uses Indentation to show function recursion depth (│   ├──).
2. 🏎️ Trace Decorator: Measures execution time and arguments of critical functions.
3. 💾 Smart Crash Dumps: Serializes variables safely into JSON when errors occur.
4. 🧠 Context Manager: `with logger.block("Name"):` for code grouping.
5. ♻️ Rotating Logs: Prevents log files from growing infinitely.

Usage:
    from kritidocx.utils.logger import logger
    
    logger.info("Starting engine...")
    
    @logger.trace("Parsing")
    def process_data(data):
        with logger.block("Validation"):
            ...
"""

import os
import logging
import json
import time
import functools
import traceback
import inspect
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Prevent circular imports: Config loaded inside init or methods where possible
try:
    from kritidocx.config.settings import AppConfig
except ImportError:
    AppConfig = None

# =========================================================================
# 🎨 COLOR CONSTANTS (Console Visuals)
# =========================================================================
class Colors:
    RESET = "\033[0m"
    BOLD  = "\033[1m"
    DIM   = "\033[2m"
    
    RED    = "\033[91m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    BLUE   = "\033[94m"
    CYAN   = "\033[96m"
    MAGENTA = "\033[95m"
    WHITE  = "\033[97m"
    GREY   = "\033[90m"
    
    # Symbols
    ICON_INFO = "ℹ️ "
    ICON_WARN = "⚠️ "
    ICON_ERR  = "❌ "
    ICON_CRIT = "🔥 "
    ICON_DEBUG = "🐛 "
    TREE_BRANCH = "├── "
    TREE_LAST   = "└── "
    TREE_PIPE   = "│   "

# =========================================================================
# 🛠️ SYSTEM LOGGER CLASS
# =========================================================================

class SystemLogger:
    """
    Advanced Wrapper around Python's standard logging module.
    Maintains a Singleton behavior pattern via the global instance.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SystemLogger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized: return
        
        # 1. State Tracking
        self.indent_level = 0
        self.trace_enabled = True # Default true until config loaded
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 2. Config Loading (Safe Default paths if config module fail)
        self.log_dir = "logs"
        self.dump_dir = os.path.join("logs", "crash_dumps")
        
        if AppConfig:
            self.log_dir = AppConfig.LOG_DIR
            self.dump_dir = AppConfig.CRASH_DUMP_DIR
            self.trace_enabled = getattr(AppConfig, 'DEBUG', True)

        # 2. Log Dir Resolution (सुरक्षित लॉगिंग)
        # Check if self.log_dir is not None before passing to os.path.exists
        if self.log_dir and not os.path.exists(self.log_dir):

            try:
                # केवल तभी फोल्डर बनाएं अगर 'DEBUG' मोड ऑन हो (Development में)
                # लाइब्रेरी के रूप में चलते समय यह यूजर की मशीन पर कचरा नहीं करेगा
                if getattr(AppConfig, 'DEBUG', False):
                    os.makedirs(self.log_dir, exist_ok=True)
                else:
                    self.log_dir = None # फोल्डर नहीं है तो फाइल लॉगिंग बंद करें
            except:
                # यदि फोल्डर बनाने की अनुमति नहीं है (Permission Error)
                self.log_dir = None 

        # 3. Dump Dir Check
        if self.log_dir and not os.path.exists(self.dump_dir):
            try:
                os.makedirs(self.dump_dir, exist_ok=True)
            except:
                pass

        # 4. Initialize Internal Logger
        # (इसके बाद सेटअप फंक्शन कॉल होगा)
        self._setup_internal_logger()
        
        self._initialized = True
        self.info(f"🚀 System Logger Initialized (Session: {self.session_id})")

    def _setup_internal_logger(self):
        """Sets up handlers (File Rotating & Console Stream) based on Settings."""
        self._core_logger = logging.getLogger("MyDocX_Core")
        self._core_logger.propagate = False 
        self._core_logger.handlers = []     

        # 1. 🛡️ Determine the Log Level based on Config

        target_level = logging.CRITICAL # डिफ़ॉल्ट (अत्यधिक शांत)

        # अगर कॉन्फिग लोड हो चुका है
        if AppConfig:
            level_str = getattr(AppConfig, 'LOG_LEVEL', 'CRITICAL').upper()
            
            # मैपिंग (Mapping the string to actual logging level)
            if level_str == 'DEBUG' or getattr(AppConfig, 'DEBUG', False):
                target_level = logging.DEBUG
                self.trace_enabled = True
            elif level_str == 'INFO':
                target_level = logging.INFO
            elif level_str == 'WARNING':
                target_level = logging.WARNING
            elif level_str == 'ERROR':
                target_level = logging.ERROR
            elif level_str == 'NONE' or level_str == 'CRITICAL':
                target_level = logging.CRITICAL
                # अगर NONE है तो हम एक और लेयर का म्यूट कर सकते हैं 
                # (अभी के लिए CRITICAL पर्याप्त है जो INFO को रोक देगा)

        # लॉगर का स्तर सेट करें
        self._core_logger.setLevel(target_level)
        self._core_logger.handlers =[]     

        # A. File Handler (केवल तभी बनाएँ जब log_dir मौजूद हो)
        if self.log_dir:
            try:
                log_file = os.path.join(self.log_dir, "session_latest.log")
                fh = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
                fh.setFormatter(logging.Formatter(
                    '%(asctime)s | %(levelname)-8s | %(message)s', 
                    datefmt='%H:%M:%S'
                ))
                self._core_logger.addHandler(fh)
            except Exception:
                pass # अगर Vercel पर फाइल बनाने में कोई एरर आये तो इग्नोर करें

        # B. Console Handler (Standard Output) - यह हमेशा काम करेगा
        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter('%(message)s'))
        self._core_logger.addHandler(ch)
        
    # =========================================================================
    # 🌲 HIERARCHY & INDENTATION UTILS
    # =========================================================================

    def _get_indent_str(self):
        """Generates visual tree bars based on depth."""
        if self.indent_level <= 0: return ""
        return (Colors.DIM + Colors.WHITE + (Colors.TREE_PIPE * self.indent_level) + Colors.RESET)

    def context_block(self, name):
        """Returns a context manager to auto-indent code blocks."""
        return _LogContextManager(self, name)

    # Alias for prettier usage
    block = context_block

    # =========================================================================
    # 📝 STANDARD LOGGING METHODS
    # =========================================================================

    def info(self, msg):
        """General information flow."""
        formatted = f"{self._get_indent_str()}{Colors.GREEN}{Colors.ICON_INFO}{msg}{Colors.RESET}"
        self._core_logger.info(formatted)

    def warning(self, msg):
        """Non-fatal issues."""
        formatted = f"{self._get_indent_str()}{Colors.YELLOW}{Colors.BOLD}{Colors.ICON_WARN}{msg}{Colors.RESET}"
        self._core_logger.warning(formatted)

    def error(self, msg):
        """Failures that don't stop the system."""
        formatted = f"{self._get_indent_str()}{Colors.RED}{Colors.BOLD}{Colors.ICON_ERR}{msg}{Colors.RESET}"
        self._core_logger.error(formatted)

    def critical(self, msg):
        """System stopping errors."""
        formatted = f"{self._get_indent_str()}{Colors.RED}{Colors.BOLD}█▀█ {Colors.ICON_CRIT}{msg.upper()} █▀█{Colors.RESET}"
        self._core_logger.critical(formatted)

    def debug(self, msg):
        """Deep dive info (Enabled via config)."""
        if self.trace_enabled:
            formatted = f"{self._get_indent_str()}{Colors.DIM}{Colors.CYAN}{Colors.ICON_DEBUG}{msg}{Colors.RESET}"
            self._core_logger.debug(formatted)

    # =========================================================================
    # 🕵️ TRACE DECORATOR
    # =========================================================================

    def trace(self, segment="OP"):
        """
        Decorator: Logs Entry -> Exit, Arguments, Duration and Error Dumping.
        Usage: @logger.trace("Parsing")
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if not self.trace_enabled:
                    return func(*args, **kwargs)

                fn_name = func.__name__
                
                # 1. Prepare Arguments for display (Shorten large objects)
                pretty_args = self._sanitize_args(args, kwargs)
                
                # 2. Log Entry
                indent_bars = self._get_indent_str()
                self._core_logger.info(f"{indent_bars}{Colors.DIM}{Colors.TREE_BRANCH}{Colors.BLUE}{fn_name}{Colors.RESET}({pretty_args}) [{segment}]")
                
                self.indent_level += 1 # ⬇️ Indent In
                start_time = time.perf_counter()
                
                try:
                    # 3. Execute Function
                    result = func(*args, **kwargs)
                    
                    # 4. Log Success
                    elapsed = (time.perf_counter() - start_time) * 1000
                    
                    # Decrement logic handled first to align 'RETURN' branch
                    self.indent_level -= 1 # ⬆️ Indent Out
                    indent_bars = self._get_indent_str() # Re-calc bars
                    
                    # Shorten Result string
                    res_summary = self._serialize_obj(result)[:100]
                    if len(str(result)) > 100: res_summary += "..."
                    
                    self._core_logger.debug(f"{indent_bars}{Colors.DIM}{Colors.TREE_LAST}{Colors.GREEN}Return{Colors.RESET}: {res_summary} ({elapsed:.2f}ms)")
                    
                    return result

                except Exception as e:
                    self.indent_level -= 1 # ⬆️ Indent Out
                    
                    # 5. Handle Crash
                    dump_path = self.create_crash_dump(e, context_vars={
                        "function": fn_name,
                        "args": str(args)[:500], 
                        "kwargs": str(kwargs)[:500],
                        "trace": traceback.format_exc()
                    })
                    
                    self.critical(f"CRASH in '{fn_name}': {e}")
                    self.warning(f"Dump saved at: {dump_path}")
                    raise e # Re-raise for pipeline to catch

            return wrapper
        return decorator

    # =========================================================================
    # 🧠 SERIALIZATION & DUMP LOGIC
    # =========================================================================

    def create_crash_dump(self, exception_obj, context_vars=None):
        """
        Generates a JSON file capturing the state during an exception.
        """
        # 🛑 BUG FIX: If dump_dir is None (like in Vercel), abort writing local dump file
        if not self.dump_dir:
            return "[Dump Aborted: Read-Only Env]"

        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"CRASH_{timestamp}.json"
        full_path = os.path.join(self.dump_dir, filename)
        
        try:
            payload = {
                "error_type": type(exception_obj).__name__,
                "message": str(exception_obj),
                "timestamp": str(datetime.now()),
                "context": context_vars or {},
                "stack_trace": traceback.format_exc()
            }
            
            # Using custom encoder needed? Stringify everything safer.
            with open(full_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=4, default=lambda x: f"<{type(x).__name__}>")
                
            return full_path
        except Exception as dump_err:
            return f"[Dump Failed: {dump_err}]"

    def _sanitize_args(self, args, kwargs):
        """Clean arguments representation for console output."""
        summary = []
        
        # Args
        for arg in args:
            val = self._serialize_obj(arg)
            summary.append(val)
            
        # Kwargs
        for k, v in kwargs.items():
            val = self._serialize_obj(v)
            summary.append(f"{k}={val}")
            
        return ", ".join(summary)

    def _serialize_obj(self, obj):
        """Smart Object to String converter."""
        # 1. BeautifulSoup Tags
        if hasattr(obj, 'name') and hasattr(obj, 'attrs'):
            # It's an HTML Tag
            ids = f" id='{obj['id']}'" if obj.has_attr('id') else ""
            cls = f" class='{obj['class']}'" if obj.has_attr('class') else ""
            return f"<{obj.name}{ids}{cls}>"
        
        # 2. Large Strings
        s_obj = str(obj)
        if len(s_obj) > 60:
            return s_obj[:60] + "..."
            
        return s_obj

# =========================================================================
# 🔄 CONTEXT MANAGER HELPER
# =========================================================================

class _LogContextManager:
    """Helper to handle indentation in `with logger.block(...)` blocks."""
    def __init__(self, logger_instance, name):
        self.logger = logger_instance
        self.name = name
        self.start_time = 0

    def __enter__(self):
        indent = self.logger._get_indent_str()
        # Print "Header" of block
        self.logger._core_logger.info(f"{indent}{Colors.BOLD}{Colors.MAGENTA}┌── [BLOCK: {self.name}]{Colors.RESET}")
        self.logger.indent_level += 1
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (time.perf_counter() - self.start_time) * 1000
        self.logger.indent_level -= 1
        indent = self.logger._get_indent_str()
        
        if exc_type:
            # Error inside block
            self.logger._core_logger.error(f"{indent}{Colors.BOLD}{Colors.RED}└── [FAILED: {self.name}]{Colors.RESET} ({duration:.2f}ms)")
        else:
            # Success block end
            self.logger._core_logger.info(f"{indent}{Colors.BOLD}{Colors.MAGENTA}└── [END: {self.name}]{Colors.RESET} ({duration:.2f}ms)")

# =========================================================================
# 🌍 GLOBAL INSTANCE
# =========================================================================
logger = SystemLogger()