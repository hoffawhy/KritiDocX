"""
PARSERS PACKAGE (The Input Reader Layer)
----------------------------------------
यह पैकेज कच्चे इनपुट (HTML, Markdown) को पढ़ने, साफ़ करने और
`Core Router` के लिए तैयार करने की जिम्मेदारी निभाता है।

Modules:
1. HtmlParser: मुख्य इंजन जो DOM ट्री को स्कैन करता है।
2. MarkdownParser: एक प्री-प्रोसेसर जो MD को HTML में बदलता है (Math Safe).
3. InputSanitizer: एक सफाई कर्मी जो टूटे हुए HTML और हानिकारक स्क्रिप्ट्स हटाता है।

Usage in Pipeline:
    from kritidocx.parsers import HtmlParser
    parser = HtmlParser(router)
    parser.parse_file("report.html")
"""

# 1. The Main HTML Reader
from .html_parser import HtmlParser

# 2. The Markdown Converter Wrapper
from .markdown_parser import MarkdownParser

# 3. The Utility Helper (Exposed for manual cleanup if needed)
from .sanitizer import InputSanitizer

# Explicitly export the public classes
__all__ = [
    'HtmlParser',
    'MarkdownParser',
    'InputSanitizer'
]