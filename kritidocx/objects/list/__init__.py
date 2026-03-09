"""
LIST OBJECTS PACKAGE (The Numbering System)
-------------------------------------------
This package handles the logic for converting HTML lists (<ul>, <ol>) into
native Microsoft Word Numbering/Bullets using the 'numbering.xml' part.

Architecture:
1. Controller: 'ListController' is the main entry point used by the Router.
2. Manager: 'NumberingManager' handles the raw XML injection of definitions.
3. Internals: 'StyleFactory' (Visuals) and 'IndentMath' (Geometry) are 
   encapsulated internally.

Usage:
    from kritidocx.objects.list import ListController
    lc = ListController(doc)
    lc.process_list(node, ...)
"""

# The Main Orchestrator (Used by Core Router)
from .list_controller import ListController

# The Backend XML Manager (Exposed for low-level extensions if needed)
from .numbering_manager import NumberingManager

# Explicitly define Public API
__all__ = [
    'ListController',
    'NumberingManager'
]