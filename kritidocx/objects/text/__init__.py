"""
TEXT OBJECTS PACKAGE (The Content Core)
---------------------------------------
यह पैकेज दस्तावेज़ के सभी टेक्स्ट-संबंधित तत्वों (Text Elements) को संभालता है।
इसे "Block Level" (Paragraphs) और "Inline Level" (Runs) लॉजिक को अलग-अलग
रखने के लिए डिज़ाइन किया गया है।

Modules Included:
1. ParagraphManager: Alignment, Indentation, Borders, Spacing.
2. RunManager: Fonts, Colors, Shading, Effects (Bold/Italic).
3. HeadingManager: Document Structure, TOC Levels, Bookmarking.
4. HyperlinkManager: Internal Navigation & Web Links.
5. BreakManager: Layout Flow (Line/Page/Column Breaks).
"""

# Import core managers relative to this package
from .paragraph_manager import ParagraphManager
from .run_manager import RunManager
from .heading_manager import HeadingManager
from .hyperlink_manager import HyperlinkManager
from .break_manager import BreakManager

# Explicitly define what is available to the outside world
# यह सुनिश्चित करता है कि 'from kritidocx.objects.text import *' करने पर
# केवल जरूरी क्लासेस ही लोड हों, अंदरूनी हेल्पर फंक्शन्स नहीं।
__all__ = [
    'ParagraphManager',
    'RunManager',
    'HeadingManager',
    'HyperlinkManager',
    'BreakManager'
]