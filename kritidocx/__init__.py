"""
🚀 KritiDocX Library
--------------------
Convert HTML and Markdown into high-fidelity Microsoft Word documents.

Usage:
    from kritidocx import convert_document
    convert_document("input.html", "output.docx")
"""

import sys
import os

# --- VERSIONING ---
__version__ = "0.1.0.dev6"
__author__ = "KritiDocX Team"

# --- INTERNAL IMPORTS ---
# यूजर को सीधे internal modules न देखने पड़ें, इसलिए हम केवल जरूरी चीजें ही एक्सपोज करेंगे।
from .core.pipeline import Pipeline

from .exceptions import KritiDocXError, InputNotFoundError

# =========================================================
# 🔓 PUBLIC FACADE FUNCTION (Main Entry Point)
# =========================================================

from typing import Optional, Dict

def convert_document(
    input_file: str, 
    output_file: Optional[str] = None, 
    data_source: Optional[str] = None, 
    config: Optional[Dict] = None
) -> bool:
    """
    Converts HTML or Markdown files into Microsoft Word documents natively.

    Args:
        input_file (str): The main file path to parse (.html or .md).
        output_file (Optional[str], default=None): Destination `.docx` file path. 
                                  If None, saves next to input.
        data_source (Optional[str], default=None): A Markdown content file to 
                                  inject into a template (`input_file`).
        config (Optional[Dict], default=None): Override settings dictionary 
                                  (e.g., {'DEBUG': True}).

    Returns:
        bool: True if the document generated successfully, False otherwise.
    
    Raises:
        InputNotFoundError: If `input_file` cannot be located on disk.
        ConversionFailedError: If processing crashes internally.
    """
    
    # 1. Pipeline instance बनाएँ
    engine = Pipeline(config=config)
    
    # 2. Run करें
    result = engine.run(input_file, output_file, data_source)
    
    return result

# =========================================================
# 📦 EXPORT LIST
# =========================================================
# 'from kritidocx import *' केवल इन्हीं दो को दिखाएगा
__all__ = [
    'convert_document', 
    'Pipeline',
    'KritiDocXError', 
    'InputNotFoundError',
    '__version__'
]