"""
TABLE OBJECTS PACKAGE (The Grid Engine)
---------------------------------------
This package handles the conversion of HTML Tables into MS Word Tables.

Architecture:
1. Controller: The orchestrator (`TableController`).
2. Matrix Engine: Solves Rowspan/Colspan logic (`MatrixEngine`).
3. Managers: Decorators for Rows, Cells, and Table Properties.

Usage:
    from kritidocx.objects.table import TableController
    controller = TableController(doc)
    controller.process_table(node, container, ...)
"""

# The Main Interface (Router uses this)
from .table_controller import TableController

# Exposed Utility (Useful for debuggers/analyzers to see the grid structure without rendering)
from .matrix_engine import MatrixEngine

# Explicit API Definition
__all__ = [
    'TableController',
    'MatrixEngine'
]