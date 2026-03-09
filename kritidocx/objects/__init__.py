"""
OBJECTS DOMAIN PACKAGE (The Logic Core)
---------------------------------------
This package aggregates all specific Domain Logics for MS Word elements.
It acts as the single source of truth for all Content Generators.

Layer Hierarchy:
    [Core (Router)] -> calls -> [Objects (Managers)] -> calls -> [XML Factory (Writers)]

Exports:
    - Text: Paragraphs, Runs, Links, Breaks, Headings.
    - Table: Grids, Cells, Rows.
    - Media: Images, Textboxes, Shapes.
    - Layout: Pages, Sections, Headers/Footers.
    - List: Bullets, Numbering.
    - Form: Inputs, Checkboxes.
    - Math: Equations.
"""

# =========================================================================
# 1. 📝 TEXT COMPONENTS (Content & Typography)
# =========================================================================
from .text import (
    ParagraphManager,
    RunManager,
    HeadingManager,
    HyperlinkManager,
    BreakManager
)

# =========================================================================
# 2. ▦ TABLE COMPONENTS (Grids & Structures)
# =========================================================================
from .table import (
    TableController,
    MatrixEngine  # Exposed for debugging complex grid logic
)

# =========================================================================
# 3. 🖼️ MEDIA COMPONENTS (Visual Assets)
# =========================================================================
from .media import (
    MediaController,
    ImageLoader   # Exposed so Layout/Background logic can fetch images
)

# =========================================================================
# 4. 📄 LAYOUT COMPONENTS (Page & Sections)
# =========================================================================
from .layout import (
    SectionManager,
    PageSetup,
    MarginManager,
    ColumnManager,
    HeaderFooterManager
)

# =========================================================================
# 5. 🔢 LIST COMPONENTS (Bullets & Numbering)
# =========================================================================
from .list import (
    ListController,
    NumberingManager
)

# =========================================================================
# 6. 🎛️ FORM COMPONENTS (Interactive SDT)
# =========================================================================
from .form import (
    FormController,
    CheckboxHandler, # Useful if someone needs direct access to specific handler
    DropdownHandler
)

# =========================================================================
# 7. 🧮 MATH COMPONENTS (Equations)
# =========================================================================
from .math import (
    MathController,
    LatexParser
)

# =========================================================================
# 🔒 PUBLIC API DEFINITION
# =========================================================================
__all__ = [
    # Text
    'ParagraphManager', 'RunManager', 'HeadingManager', 'HyperlinkManager', 'BreakManager',
    
    # Table
    'TableController', 'MatrixEngine',
    
    # Media
    'MediaController', 'ImageLoader',
    
    # Layout
    'SectionManager', 'PageSetup', 'MarginManager', 'ColumnManager', 'HeaderFooterManager',
    
    # List
    'ListController', 'NumberingManager',
    
    # Form
    'FormController', 'CheckboxHandler', 'DropdownHandler',
    
    # Math
    'MathController', 'LatexParser'
]