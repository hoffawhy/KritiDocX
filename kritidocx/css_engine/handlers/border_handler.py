"""
BORDER HANDLER (The Boundary Architect)
---------------------------------------
Responsible for resolving Border Shorthands (1px solid red).
CRITICAL: Handles 'transparent' logic conflicts correctly.
"""

import re
from kritidocx.basics.color_manager import ColorManager
from kritidocx.basics.unit_converter import UnitConverter
from kritidocx.config.theme import ThemeConfig

class BorderHandler:
    
    # CSS Style Name -> Word XML Enum Map
    # (Matches old theme config logic but centralized here for speed)
    STYLE_MAP = ThemeConfig.BORDER_STYLE_MAP

    # Width Keywords -> Eighths of point
    WIDTH_KEYWORDS = {
        'thin': 4,      # 0.5pt
        'medium': 12,   # 1.5pt
        'thick': 24     # 3.0pt
    }

    @staticmethod
    def process(prop, value, attributes_dict):
        """
        Parses inputs like 'border', 'border-left', 'border: 1px solid red'.
        Injects a dictionary representing Word XML border attributes.
        """
        if not value: return

        # 1. PRE-CHECK: Shorthand Expansion (border -> top, bottom, left, right)
        # अगर यह ग्लोबल 'border' है, तो इसे चारों दिशाओं के लिए प्रोसेस करें
        if prop == 'border':
            data = BorderHandler._parse_single_string(value)
            # Apply to all sides implicitly handled by assigning data to dict keys
            # But the caller (CssEngine) needs specific keys or generic object
            # CSS Logic: 'border' sets all 4.
            # We store the *parsed data object* so Object Handlers can use it efficiently
            
            # हालांकि, हमारे मौजूदा XML Writers (Table/Para) 'border-top' वगैरह मांगते हैं।
            # इसलिए हम इसे 4 कीज़ में डुप्लिकेट कर देते हैं।
            attributes_dict['border-top'] = data
            attributes_dict['border-bottom'] = data
            attributes_dict['border-left'] = data
            attributes_dict['border-right'] = data
            # मूल स्ट्रिंग भी रखें (रेफरेंस के लिए)
            attributes_dict['border'] = data 
            return

        # 2. Specific Side (border-left, etc.)
        if prop.startswith('border-'):
            attributes_dict[prop] = BorderHandler._parse_single_string(value)

    @staticmethod
    def _parse_single_string(border_str):
        """
        Logic Core: '1px solid transparent' -> {'val': 'nil', 'sz': 0 ...}
        """
        raw = str(border_str).strip().lower()
        
        # 🟢 [CRITICAL CONFLICT FIX]: Transparent Priority
        # यदि शब्द 'transparent' मौजूद है, तो बिना आगे बढ़े इसे अदृश्य घोषित करें।
        # इससे 'solid' या 'width' का कोई असर नहीं होगा।
        if 'transparent' in raw or 'none' in raw or 'hidden' in raw:
            return {'val': 'nil', 'sz': 0, 'color': 'auto', 'space': 0}

        # --- Default Structure ---
        border_props = {
            'val': 'single', # Default assumption until proven otherwise
            'sz': 4,         # Default 0.5pt width
            'color': 'auto', # Default black
            'space': 0
        }

        # Tokenization Strategy: Split by space, but respect functions (rgb) logic?
        # For simplicity, and speed, generic splitting works well for borders usually.
        # (Color Manager helps filtering hex)
        
        # --- A. Extract Color ---
        # हम अपनी ColorManager का उपयोग करके रंग ढूँढेंगे
        # Color finding logic: Split and test chunks? Or Regex?
        # Regex is safer to extract '#ABC' or 'red'
        
        found_color_hex = None
        # Try Hex
        # --- NEW LOGIC: Extract Complex Color Functions first ---
        # यह regex कोष्ठक वाली पूरी वैल्यू (rgb/rgba/hsl/hsla) को एक बार में उठा लेगा
        complex_color_match = re.search(r'(?:rgba?|hsla?)\([^\)]+\)', raw)
        if complex_color_match:
            found_color_str = complex_color_match.group(0)
            found_color_hex = ColorManager.get_hex(found_color_str)
            # स्ट्रिंग से कलर निकाल लें ताकि बाकी का हिस्सा (width/style) आसानी से split हो सके
            raw = raw.replace(found_color_str, '').strip()
        
        # बाकी का लॉजिक (Hex check और Split) जैसा पहले था:
        if not found_color_hex:
            hex_match = re.search(r'#(?:[0-9a-f]{3}){1,2}', raw)
            if hex_match:
                found_color_hex = ColorManager.get_hex(hex_match.group(0))
                raw = raw.replace(hex_match.group(0), '').strip()
        
        # --- NEW: Named Color Extraction (red, blue, etc.) ---
        if not found_color_hex:
            temp_tokens = raw.split()
            for token in temp_tokens:
                # यदि टोकन कोई बॉर्डर स्टाइल नहीं है (जैसे 'wavy'), तो इसे कलर मानें
                if token not in BorderHandler.STYLE_MAP:
                    # ColorManager से चेक करें कि क्या यह एक मान्य रंग का नाम है
                    possible_hex = ColorManager.get_hex(token)
                    # '000000' चेक को हटा दें ताकि शुद्ध 'black' कलर भी काम करे
                    # हम केवल तभी रंग बदलेंगे जब ColorManager को मान्य नाम मिले (जो डिफ़ॉल्ट न हो)
                    if possible_hex and possible_hex != ColorManager.DEFAULT_HEX:
                        found_color_hex = possible_hex
                        raw = raw.replace(token, '').strip() # टोकन साफ़ करें
                        break
                    # यदि यूजर ने "black" लिखा है, तो उसे मैन्युअली स्वीकार करें
                    elif token.lower() == 'black':
                        found_color_hex = '000000'
                        raw = raw.replace(token, '').strip()
                        break

        if found_color_hex:
            border_props['color'] = found_color_hex



        # --- B. Extract Style ---
        # Remaining raw string has width and style.
        tokens = raw.split()
        for token in tokens:
            if token in BorderHandler.STYLE_MAP:
                border_props['val'] = BorderHandler.STYLE_MAP[token]
                break # First style keyword wins

        # --- C. Extract Width ---
        width_found = False
        for token in tokens:
            if token in BorderHandler.WIDTH_KEYWORDS:
                border_props['sz'] = BorderHandler.WIDTH_KEYWORDS[token]
                width_found = True
                break
            # Numeric check (1px, .5pt)
            if re.match(r"^\d*\.?\d+(px|pt|em|in)?$", token):
                # Using standard Unit Converter for conversion math
                # Returns eighths (1/8 pt) directly
                border_props['sz'] = UnitConverter.to_border_eighths(token)
                width_found = True
                break
        
        # [IMPLICIT STYLE FIX]: If width > 0 but style undefined/nil, browser implies solid.
        # But our conflict fix above handled transparent/nil already.
        # Here we catch the 'border: 1px red' case (no style).
        if width_found and border_props['val'] == 'single':
            pass # Keep default

        return border_props