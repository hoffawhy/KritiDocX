"""
SETTINGS CONFIGURATION (Advanced Production Ready)
--------------------------------------------------
यह फाइल 'System Constraints' और 'Operational Behavior' को नियंत्रित करती है।
Note: डिजाइन (Colors/Fonts) के लिए 'theme.py' का उपयोग करें।
"""

import os
import sys
import platform
import tempfile  # सिस्टम टेम्परेरी फोल्डर के लिए

class AppConfig:
# ---------------------------------------------------------------
    # 1. 🏗️ INTERNAL LIBRARY PATHS (Fixed inside package)
    # ---------------------------------------------------------------
    
    # यह फाइल जहाँ है, वहाँ से रूट निकालें
    _CURRENT_FILE = os.path.abspath(__file__)
    CONFIG_DIR = os.path.dirname(_CURRENT_FILE)
    PACKAGE_ROOT = os.path.dirname(CONFIG_DIR) # kritidocx/
    
    # Internal Assets (Template XSLT etc. जो पैकेज के साथ आते हैं)
    INTERNAL_ASSETS_DIR = os.path.join(PACKAGE_ROOT, "assets")

    # ---------------------------------------------------------------
    # 2. ⚡ RUNTIME PATHS (Dynamic & Safe for Serverless)
    # ---------------------------------------------------------------
    
    # 🛑 Serverless/Vercel FIX: OS level guaranteed temporary directory mapping
    # `tempfile.gettempdir()` ensures writing into safe areas like `/tmp` globally
    try:
        TEMP_DIR = os.path.join(tempfile.gettempdir(), "kritidocx_cache")
    except Exception:
        # Ultimate fail-safe (Will trigger exception handler locally if OS broken)
        TEMP_DIR = None

    # LOGGING: We won't block system start. Set default to working dir only if possible.
    LOG_DIR = os.path.join(os.getcwd(), "logs")
    CRASH_DUMP_DIR = os.path.join(LOG_DIR, "crash_dumps")
    
    # (INPUT और HTML फोल्डर्स की अब आवश्यकता नहीं है, वे runtime argument से आएंगे)
    # OUTPUT फोल्डर का डिफ़ॉल्ट path यूज़र का करंट वर्किंग डायरेक्टरी होगा
    OUTPUT_DIR = os.getcwd()

    # =========================================================================
    # 2. ⚙️ ENGINE BEHAVIOR (इंजन व्यवहार)
    # =========================================================================
    
    # Debug Mode: True होने पर कंसोल में बहुत बारीक डिटेल्स (Tracing) दिखेंगी।
    DEBUG = False
    
    # Console Log Level (SILENT BY DEFAULT)
    # विकल्प (Options): 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'CRITICAL_ONLY', या 'NONE'
    # प्रोडक्शन लाइब्रेरी के लिए 'ERROR' या 'CRITICAL' बेस्ट है।
    LOG_LEVEL = 'CRITICAL' 

    # यदि True, तो प्रोग्राम एरर आने पर बंद नहीं होगा (Soft Fail)
    CONTINUE_ON_ERROR = False

    
    # क्रैश होने पर JSON डंप बनाना है या नहीं?
    ENABLE_CRASH_DUMPS = False
    
    # Recursion Depth: बहुत गहरे HTML नेस्टिंग (Deeply nested divs) से 
    # Python 'Maximum Recursion Depth' एरर दे सकता है। इसे यहाँ नियंत्रित करें।
    MAX_RECURSION_LIMIT = 2000

    # DEBUG SWITCHES
    # इसे True करने पर कंसोल में लिस्ट का पूरा कच्चा चिट्ठा (Raw Data) दिखेगा
    DEBUG_LISTS = False
    DEBUG_TABLES = False
    DEBUG_TEXT_LAYOUT = False
    DEBUG_FORMS = False
    
    DEBUG_MEDIA = False
    
    DEBUG_POSITIONING = False
    
    DEBUG_FLEX_LAYOUT = False
    
    DEBUG_TEXT_LAYOUT = False
    
    # =========================================================================
    # 3. 🌐 NETWORKING & MEDIA (इमेज और वेब सेटिंग्स)
    # =========================================================================
    
    # ऑनलाइन इमेज डाउनलोड करने की अधिकतम समय सीमा (Seconds)
    REQUEST_TIMEOUT = 10 
    
    # क्या इमेज को लोकल डिस्क पर सेव रखना है? (बार-बार डाउनलोड से बचने के लिए)
    CACHE_DOWNLOADED_IMAGES = True
    
    # काम पूरा होने के बाद Temp फाइलें डिलीट करें?
    CLEANUP_TEMP_FILES = True
    
    # कुछ वेबसाइट Python Script को इमेज एक्सेस नहीं देतीं। 
    # यह 'Fake User Agent' हमें एक ब्राउज़र (Chrome) की तरह दिखाता है।
    HTTP_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    # क्या हम बहुत बड़ी इमेज को प्रोसेस करने से रोकें? (0 = No Limit)
    # 10 MB limit helps avoid Memory Errors in Production servers.
    MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024  

    # =========================================================================
    # 4. 📝 OUTPUT CONTROLS (आउटपुट सेटिंग्स)
    # =========================================================================
    
    # बनने वाली फाइल का डिफ़ॉल्ट नाम (अगर user न दे)
    DEFAULT_FILENAME = "Final_Report_v1.docx"
    
    # फाइल बनने के बाद क्या उसे अपने आप खोलना है? (Windows/Mac Only)
    # सर्वर पर इसे False रखें।
    AUTO_OPEN_FILE = False
    
    # अगर फाइल पहले से मौजूद है, तो क्या उसे ओवरराइट करें?
    # False होने पर नया नाम (Report_1.docx) जनरेट होगा।
    OVERWRITE_EXISTING_FILE = True

    # =========================================================================
    # 5. 🛠️ ENVIRONMENT DIAGNOSTICS (सिस्टम जांच)
    # =========================================================================
    
    @staticmethod
    def get_system_info():
        """Returns details about the current OS context."""
        return {
            "OS": platform.system(),
            "Release": platform.release(),
            "Architecture": platform.architecture()[0],
            "Python_Version": platform.python_version()
        }

    @staticmethod
    def ensure_directories():
        """
        Creates strictly internal directories needed for processing (Cache/Logs).
        Does NOT touch user input/output structures.
        """
        try:
            # 🛑 VERCEL SAFE-CHECK: /tmp directory creation (Avoid making .tmp files act as directories)
            if AppConfig.TEMP_DIR and not os.path.exists(AppConfig.TEMP_DIR):
                os.makedirs(AppConfig.TEMP_DIR, exist_ok=True)
            
            # Log dirs attempts (Silent handling in Read-Only spaces)
            if AppConfig.DEBUG and AppConfig.LOG_DIR:
                # Do NOT create logging directory directly in standard flow for read-only setups
                if not os.path.exists(AppConfig.LOG_DIR):
                    try:
                         os.makedirs(AppConfig.LOG_DIR, exist_ok=True)
                    except PermissionError:
                         AppConfig.LOG_DIR = None
                         AppConfig.CRASH_DUMP_DIR = None # Cancel dumps

            return True
            
        except (PermissionError, OSError) as e:
            # 🛑 CRITICAL SERVERLESS FIX: Fail silently, but cleanly disconnect variables causing crashes later
            AppConfig.TEMP_DIR = None
            return False
           
    @classmethod
    def override(cls, user_config):
        """
        Allows runtime modification of settings via dictionary.
        Usage: AppConfig.override({'DEBUG': True, 'REQUEST_TIMEOUT': 20})
        """
        if not user_config or not isinstance(user_config, dict):
            return

        for key, value in user_config.items():
            # केवल उन्हीं सेटिंग्स को अपडेट करें जो पहले से मौजूद हैं (Uppercase keys)
            if hasattr(cls, key) and key.isupper():
                setattr(cls, key, value)