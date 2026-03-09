"""
CONFIG PACKAGE INITIALIZER (The Control Room)
---------------------------------------------
यह पैकेज एप्लिकेशन की 'सेटिंग्स', 'डिजाइन थीम' और 'फिजिकल कॉन्स्टेंट्स' 
का केंद्रीय हब है।

इसे 'Singleton Configuration Pattern' की तरह डिज़ाइन किया गया है, 
ताकि पूरे प्रोजेक्ट में एक ही सत्य (Single Source of Truth) रहे।
"""

import sys
import os

# Internal Imports
from .settings import AppConfig
from .theme import ThemeConfig
from .constants import DocConstants

# =========================================================================
# 🔒 PUBLIC API (बाहरी दुनिया के लिए उपलब्ध क्लासेस)
# =========================================================================
# जब कोई `from config import *` करेगा, तो उसे सिर्फ यही तीन चीजें मिलेंगी।
__all__ = [
    'AppConfig', 
    'ThemeConfig', 
    'DocConstants', 
    'initialize_system'
]

# =========================================================================
# 🚀 BOOTSTRAP LOGIC (System Startup)
# =========================================================================

def initialize_system(silent=True): # Default set to True
    # अब यह फंक्शन केवल internal temp paths सेटअप करेगा
    try:
        AppConfig.ensure_directories()
        return True
    except:
        return False