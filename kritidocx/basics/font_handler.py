"""
FONT HANDLER MODULE (The Typographer)
-------------------------------------
Responsibility: 
Determine the correct Font Family based on:
1. CSS Style 'font-family'.
2. Content Analysis (Unicode Ranges for Hindi, CJK, Symbols).
3. Component Type (Forms require specific fonts).

This module solves the "Missing Glyphs" problem where text appears as squares [].
"""

import logging
from functools import lru_cache
from kritidocx.config.theme import ThemeConfig

logger = logging.getLogger("MyDocX_Engine")

class FontHandler:
    """
    Intelligent Font Resolution Engine.
    Maps generic CSS families to physical Word fonts and handles multi-language scripts.
    """

    # Generic CSS mappings to Windows/Office Fonts
    GENERIC_MAP = {
        'serif': 'Times New Roman',
        'sans-serif': 'Calibri',
        'monospace': 'Courier New',
        'cursive': 'Segoe Script',
        'fantasy': 'Impact'
    }

    # Unicode Ranges (Inclusive)
    RANGE_DEVANAGARI = (0x0900, 0x097F) # Hindi, Marathi, Nepali
    RANGE_CJK_MAIN   = (0x4E00, 0x9FFF) # Chinese/Japanese/Korean
    RANGE_FORMS      = [0x2610, 0x2611, 0x2612] # Checkbox symbols (☐, ☑, ☒)
    # यह रेंज मुख्य मिडिल ईस्टर्न भाषाओं को कवर करती है
    RANGE_RTL_ABROAD = (0x0590, 0x08FF)

    @classmethod
    def resolve_font_config(cls, style_dict, text_content=None):
        """
        Main API. Returns a dict mapping Word XML attributes to Font Names.
        
        Output Format:
        {
            'ascii': 'Calibri',
            'hAnsi': 'Calibri',
            'eastAsia': 'SimSun',  (Optional)
            'cs': 'Mangal',        (Complex Script)
            'hint': 'default'      (Rendering hint)
        }
        """
        # अगर style_dict None है, तो उसे खाली डिक्शनरी बना दें
        if style_dict is None: 
            style_dict = {}

        
        
        # 1. Base Font from CSS (Primary Latin Font)
        css_font_family = cls._parse_css_font_family(style_dict.get('font-family'))
        
        # Default Primary if CSS missing
        primary_font = css_font_family or ThemeConfig.FONTS_ASCII.get('body', 'Calibri')

        # Initialize Config
        font_config = {
            'ascii': primary_font,
            'hAnsi': primary_font,
            'cs': None,        # Complex Script
            'eastAsia': None,  # Asian
            'rtl': False,
            'hint': 'default'
        }

        # 2. Text Content Analysis (If text provided)
        # This handles Mixed-Language logic automatically
        if text_content:
            cls._detect_and_apply_scripts(text_content, font_config)

        # 3. Apply Overrides based on Context
        
        # Override A: Forms (Checkboxes)
        # Checkbox glyphs often fail on Calibri/Arial. Use MS Gothic.
        if text_content and any(ord(char) in cls.RANGE_FORMS for char in text_content):
            form_font = ThemeConfig.FONTS_COMPLEX.get('forms', 'MS Gothic')
            font_config['ascii'] = form_font
            font_config['hAnsi'] = form_font
            font_config['eastAsia'] = form_font
            font_config['hint'] = 'eastAsia' # Force render engine priority

        return font_config

    # -------------------------------------------------------------------------
    # INTERNAL HELPERS
    # -------------------------------------------------------------------------

    @staticmethod
    def _parse_css_font_family(font_str):
        """
        Cleans strings like: "'Helvetica Neue', Arial, sans-serif"
        Returns the first available valid font.
        """
        if not font_str: return None
        
        # Split comma-separated lists
        families = [f.strip() for f in font_str.split(',')]
        
        for fam in families:
            # Remove quotes
            clean = fam.replace("'", "").replace('"', "")
            
            # Check Generic Map
            if clean.lower() in FontHandler.GENERIC_MAP:
                return FontHandler.GENERIC_MAP[clean.lower()]
            
            # Assume it's a specific font name (e.g. "Verdana")
            # In a real desktop app, we could check os.fonts to verify existence
            return clean
            
        return None

    @classmethod
    def _detect_and_apply_scripts(cls, text, config):
        """
        Scans text for non-ascii characters and populates 'cs' or 'eastAsia'.
        Performance Optimized: Breaks loop once types are found.
        """
        has_hindi = False
        has_asian = False
        
        for char in text:
            code = ord(char)
            
            # Devanagari Check
            if not has_hindi:
                if cls.RANGE_DEVANAGARI[0] <= code <= cls.RANGE_DEVANAGARI[1]:
                    has_hindi = True
            
            # CJK Check
            if not has_asian:
                if cls.RANGE_CJK_MAIN[0] <= code <= cls.RANGE_CJK_MAIN[1]:
                    has_asian = True
            
            # [NEW] RTL Check (Arabic/Urdu/Hebrew)
            # RTL को भी 'cs' फॉन्ट स्लॉट ही चाहिए, लेकिन rtl फ्लैग के साथ।
            if not config.get('rtl'):
                if cls.RANGE_RTL_ABROAD[0] <= code <= cls.RANGE_RTL_ABROAD[1]:
                    config['rtl'] = True
                    # RTL को तुरंत cs (Complex Script) फॉन्ट की आवश्यकता होती है
                    # यदि थीम में 'arabic' फॉन्ट नहीं है, तो 'Arial' एक सुरक्षित विकल्प है
                    config['cs'] = ThemeConfig.FONTS_COMPLEX.get('arabic', 'Arial')
                    
                    # Hint को 'cs' सेट करें ताकि Word को पता चले कि इस स्क्रिप्ट को प्राथमिकता देनी है
                    config['hint'] = 'cs'
            
            # Optimization: If both found, stop scanning
            if has_hindi and has_asian:
                break
        
        # Apply Configuration
        if has_hindi:
            # Fetch Mangal from Theme
            config['cs'] = ThemeConfig.FONTS_COMPLEX.get('hindi', 'Mangal')
            
        if has_asian:
            config['eastAsia'] = ThemeConfig.FONTS_COMPLEX.get('asian', 'SimSun')