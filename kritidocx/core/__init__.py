"""
CORE PACKAGE (The Central Nervous System)
-----------------------------------------
This package coordinates all sub-systems (Parsers, Objects, XML Factory)
to perform the document conversion.

Usage:
    # Option 1: Quick Use
    from kritidocx.core import convert_document
    convert_document("input.html", "output.docx")

    # Option 2: Advanced Control
    from kritidocx.core import Pipeline
    engine = Pipeline()
    engine.run(...)
"""

# 1. Main Orchestration Engine
from .pipeline import Pipeline

# 2. Key Components (Exposed for advanced custom scripts)
from .docx_driver import DocxDriver
from .router import Router

# =========================================================================
# ⚡ CONVENIENCE WRAPPER
# =========================================================================

def convert_document(input_file, output_file=None, data_file=None):
    """
    Args:
        input_file: Primary file or HTML Template.
        output_file: Result path.
        data_file: Optional Markdown content file (activates Template Mode).
    """
    engine = Pipeline()
    # Pipeline now accepts data_source kwarg
    return engine.run(input_file, output_file, data_source=data_file)


# =========================================================================
# 🔒 PUBLIC API EXPORT
# =========================================================================
__all__ = [
    'Pipeline',
    'DocxDriver',
    'Router',
    'convert_document'
]

# System Versioning
__version__ = "3.0.0"
__author__ = "MyDocX Engine Team"