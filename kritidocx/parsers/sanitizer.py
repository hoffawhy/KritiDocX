"""
INPUT SANITIZER (The Cleaning Crew)
-----------------------------------
Responsibility:
Pre-processes raw HTML text before it hits BeautifulSoup.
Ensures data hygiene by removing scripts, comments, and invalid control characters.

Problem:
1. XML cannot handle certain null/control characters found in raw HTML.
2. Scripts/Comments clutter the DOM tree unnecessarily.
3. Invisible unicode (like Zero Width Spaces) causes 'Invalid File' errors in Word.

Features:
- Regex-based removal of Javascript (<script>).
- Safe stripping of HTML Comments.
- Artifact cleaning (\u200b, \xa0 normalized).
"""

import re
import logging

# Fallback logger
try:
    from kritidocx.utils.logger import logger
except ImportError:
    import logging
    logger = logging.getLogger("MyDocX_Parser")

class InputSanitizer:
    """
    Static utility to scrub HTML content strings.
    """

    # 1. Regex patterns (Compiled for performance)
    _SCRIPT_PATTERN = re.compile(r'<(script|noscript|object|embed).*?>.*?</\1>', re.DOTALL | re.IGNORECASE)
    _COMMENT_PATTERN = re.compile(r'<!--.*?-->', re.DOTALL)
    _STYLE_PATTERN = re.compile(r'<style.*?>.*?</style>', re.DOTALL | re.IGNORECASE)
    
    # 2. Invisible junk characters often found in copy-pasted web content
    _GARBAGE_CHARS = {
        '\u200b': '',  # Zero-width space (The XML killer)
        '\u200c': '',  # Zero-width non-joiner
        '\u200d': '',  # Zero-width joiner
        '\x00': '',    # Null byte
        '\x0b': '',    # Vertical Tab
        '\x0c': '',    # Form Feed
    }

    @classmethod
    def clean_html(cls, html_str, remove_styles=False):
        """
        Master cleaning method.
        
        Args:
            html_str (str): Raw HTML content.
            remove_styles (bool): If True, deletes <style>...</style> blocks. 
                                  Usually set False because we need CSSEngine to read them first.
        """
        if not html_str: 
            return ""

        clean_text = html_str

        try:
            # A. Security & Clutter Cleaning
            # 1. Remove JavaScript (Always)
            clean_text = cls._SCRIPT_PATTERN.sub('', clean_text)
            
            # 2. Remove Comments (Always)
            clean_text = cls._COMMENT_PATTERN.sub('', clean_text)
            
            # 3. Remove Styles (Optional - Only if processing body content blindly)
            if remove_styles:
                clean_text = cls._STYLE_PATTERN.sub('', clean_text)

            # B. Artifact Normalization
            # Translate invisible garbage to nothing
            # Make a translation table once for speed if high usage, 
            # but str.replace is usually fast enough for single passes.
            for char, replacement in cls._GARBAGE_CHARS.items():
                if char in clean_text:
                    clean_text = clean_text.replace(char, replacement)

            # C. XML Control Character Safe-Guard
            # Removes characters defined as invalid in XML 1.0 (ASCII 0-8, 11-12, 14-31)
            # Except whitespace logic we might want to keep \n or \t
            # (Handled simply by ascii filtering if strict, but ignoring for now for standard HTML unicode)

            # D. Whitespace Optimization (Optional)
            # We don't crush all whitespace because <pre> tags rely on it.
            # But converting MS-Word smart quotes/hyphens to standard ASCII can prevent font issues.
            clean_text = cls._normalize_punctuation(clean_text)

            return clean_text.strip()

        except Exception as e:
            logger.error(f"Sanitization Failed: {e}")
            # Fail safe: Return original text to avoid crash, let BS4 try its best
            return html_str

    @staticmethod
    def _normalize_punctuation(text):
        """
        Replaces Windows-specific 'Smart Quotes' and 'Dashes' with safe equivalents.
        This prevents 'Box' glyphs if the selected font (e.g. Courier) lacks high-range unicode.
        """
        replacements = {
            '\u2018': "'",  # Left Single Quote
            '\u2019': "'",  # Right Single Quote
            '\u201c': '"',  # Left Double Quote
            '\u201d': '"',  # Right Double Quote
            '\u2013': '-',  # En Dash
            '\u2014': '--', # Em Dash
            '\u2026': '...', # Ellipsis
            # Add Non-breaking space check? 
            # Note: We prefer to KEEP \xa0 for table alignment logic, handled in text processor.
        }
        
        for char, repl in replacements.items():
            if char in text:
                text = text.replace(char, repl)
        
        return text

    @staticmethod
    def strip_outer_wrappers(html_str):
        """
        Helper: Removes <html><body>...</body></html> wrappers 
        if inserting a fragment into an existing doc.
        """
        match = re.search(r'<body.*?>(.*?)</body>', html_str, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return html_str