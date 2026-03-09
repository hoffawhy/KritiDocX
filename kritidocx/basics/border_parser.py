"""
BORDER PARSER MODULE (The Boundary Architect)
---------------------------------------------
Responsibility: 
Parsing mixed-up CSS border shorthands into strict Word XML Attributes.

Problem: CSS is flexible ('1px solid red' == 'red solid 1px').
Solution: Extraction-based parsing logic (Find Color -> Find Size -> Find Style).

Target Units:
- Width: Eighths of a point (1/8 pt).
- Color: Hex (RRGGBB).
- Style: Word OOXML Enum (single, dashed, etc).
"""

import re
import logging
from kritidocx.config.theme import ThemeConfig
from kritidocx.basics.unit_converter import UnitConverter
from kritidocx.basics.color_manager import ColorManager

logger = logging.getLogger("MyDocX_Engine")

class BorderParser:
    """
    Intelligent extraction engine for border properties.
    """

    # Keywords for named widths in CSS
    WIDTH_KEYWORDS = {
        'thin': 4,      # 0.5pt (Minimum visible in Word)
        'medium': 12,   # 1.5pt
        'thick': 24     # 3.0pt
    }

    # Default if info is missing
    DEFAULT_BORDER = {
        'val': 'single', # Solid line
        'sz': 4,         # 0.5 pt
        'color': 'auto', # Black/Auto
        'space': 0
    }

    @classmethod
    def parse(cls, border_str):
        """
        Converts '1px solid #F00' to {'val': 'single', 'sz': 6, 'color': 'FF0000'}.
        """
        # सुरक्षा लेयर 1: Genuine Dictionary Check
        # यदि CSS इंजन पहले ही इसे प्रोसेस कर चुका है, तो तुरंत वापस करें।
        if isinstance(border_str, dict):
            return border_str
        
        # सुरक्षा लेयर 2: Type Guard
        # सुनिश्चित करें कि इनपुट एक स्ट्रिंग है। अगर None या कोई और टाइप है, तो वापस जाएँ।
        if not border_str or not isinstance(border_str, str):
            return None

        # सुरक्षा लेयर 3: Stringified Dictionary Protection (हार्डकोर फिक्स)
        # आपके लॉग्स बताते हैं कि कभी-कभी स्ट्रिंग "{'val': 'single'...}" जैसी आती है।
        # इसे गलती से फिर से Regex पार्सिंग में जाने से बचाना ज़रूरी है।
        clean_str = border_str.strip()
        if clean_str.startswith('{') and 'val' in clean_str:
            try:
                import ast
                # इसे वापस डिक्शनरी में बदलकर रिटर्न कर दें
                return ast.literal_eval(clean_str)
            except:
                return None

        # अब पार्सिंग के लिए आगे बढ़ें...
        raw = clean_str.lower()

        # 1. Quick Exit for Hidden/None
        if raw in ['none', 'hidden', '0', '0px', 'initial']:
            return {'val': 'nil', 'sz': 0, 'color': 'auto', 'space': 0}

        # Initialize result with defaults logic
        # (Default is single, black, 4 eighths if partially parsed)
        result = cls.DEFAULT_BORDER.copy()

        # Transparent Check: अगर 'transparent' लिखा है, तो बॉर्डर का दिखना बंद करें।
        if 'transparent' in raw:
            result['val'] = 'nil' # यह XML में <w:bottom w:val="nil"/> बनाएगा
            result['color'] = 'auto'
            # Width/Size अभी भी Parse कर सकते हैं लेकिन val='nil' रेंडरिंग रोक देगा।
            # Return immediately नहीं करेंगे, ताकि आगे width वगैरह Parse हो जाए (HTML logic)।

        # --------------------------------------------------------
        # PHASE 1: COLOR EXTRACTION
        # --------------------------------------------------------
        # पहले Color ढूंढें और निकाल लें ताकि बाद में string clean हो जाए।
        
        found_color_hex = None
        
        # A. [UPDATED FIX]: Advanced Color Function Extraction (RGBA + HSLA)
        # 1. Complex colors contains spaces, preventing safe splitting later.
        #    Example: "5px solid rgba(255, 0, 0, 0.5)"
        # Regex matches: rgba(...) OR hsla(...)
        
        # '?:' का मतलब है non-capturing group (rgba या hsla)
        complex_match = re.search(r"(?:rgba?|hsla?)\([^)]+\)", raw, re.IGNORECASE)
        
        if complex_match:
            color_str = complex_match.group(0)
            # यह ColorManager.get_hex को कॉल करेगा
            # जो अब अल्फा ब्लेंडिंग (Transparency -> Solid Mix) और HSL दोनों को संभाल सकता है।
            found_color_hex = ColorManager.get_hex(color_str)
            
            # स्ट्रिंग को साफ करें ताकि 'solid' और 'px' बचे रहें
            raw = raw.replace(color_str, "").strip()
            
        # B. Check Hex Regex
        if not found_color_hex:
            hex_match = re.search(r"#(?:[0-9a-f]{3}){1,2}", raw)
            if hex_match:
                hex_val = hex_match.group(0)
                found_color_hex = ColorManager.get_hex(hex_val)
                raw = raw.replace(hex_val, "").strip()

        # C. Check Named Colors (from ThemeConfig or Standard List)
        # We split remaining string to check words
        tokens = raw.split()
        remaining_tokens = []
        
        for token in tokens:
            # If color already found, just keep token
            if found_color_hex:
                remaining_tokens.append(token)
                continue
            
            # Check if this token is a valid color name
            # (Excluding border styles like 'orange' vs 'solid')
            if token not in ThemeConfig.BORDER_STYLE_MAP:
                possible_hex = ColorManager.get_hex(token)
                # If manager returns specific Hex (and not Default Black fallthrough)
                # Check specific override logic: 'solid' is not a color.
                if possible_hex and possible_hex != "000000": 
                    found_color_hex = possible_hex
                    continue # Don't add to remaining
                
                # Check if it was explicitly "black"
                if token == "black":
                    found_color_hex = "000000"
                    continue

            remaining_tokens.append(token)

        # Apply Found Color
        if found_color_hex:
            result['color'] = found_color_hex
        
        # --------------------------------------------------------
        # PHASE 2: WIDTH (SIZE) EXTRACTION
        # --------------------------------------------------------
        # Now parse what's left in 'remaining_tokens'
        
        final_tokens_for_style = []
        width_found = False
        
        for token in remaining_tokens:
            if width_found:
                final_tokens_for_style.append(token)
                continue

            # A. Check Keyword (thin, thick)
            if token in cls.WIDTH_KEYWORDS:
                result['sz'] = cls.WIDTH_KEYWORDS[token]
                width_found = True
                continue
                
            # B. Check Digits (1px, .5pt, 3)
            # Match number followed by optional unit
            if re.match(r"^\d*\.?\d+(px|pt|em|rem|pc|cm|mm|in)?$", token):
                # Call UnitConverter specific method
                eighths = UnitConverter.to_border_eighths(token)
                result['sz'] = eighths
                width_found = True
                continue
                
            final_tokens_for_style.append(token)

        # --------------------------------------------------------
        # PHASE 3: STYLE EXTRACTION
        # --------------------------------------------------------
        for token in final_tokens_for_style:
            # Check keys in the UPDATED map
            if token in ThemeConfig.BORDER_STYLE_MAP:
                result['val'] = ThemeConfig.BORDER_STYLE_MAP[token]
                
                # Logic Update: 
                # Word 'double' borders require slightly thicker width to be visible usually.
                if result['val'] == 'double' and result['sz'] < 6:
                     result['sz'] = 6 # Auto-bump to 0.75pt so gaps are visible
                     
                break


# ========================================================
        # PHASE 4: FINAL VALIDATION & SAFETY (REFINED)
        # ========================================================
        
        # 1. 🛑 TOTAL SILENCE: 0px, 'none' या 'transparent' को पूरी तरह बंद करें
        # 'raw' का उपयोग करके स्ट्रिंग लेवल पर भी जाँचें कि क्या उसे गायब होना चाहिए
        is_effectively_none = (
            result['sz'] == 0 or 
            result['val'] in ['nil', 'none', 'hidden'] or
            'transparent' in raw or 'none' in raw or '0px' in raw
        )

        if is_effectively_none:
            result['val'] = 'nil'    # वर्ड XML में 'nil' का मतलब है कोई रेंडरिंग नहीं
            result['sz'] = 0         # साइज ज़ीरो
            result['color'] = 'auto' # कचरा कलर्स साफ़ करें
            return result            # यहीं से वापस जाएँ

        # 2. 🌊 COMPLEX STYLE VISIBILITY: Double और Wavy को 'भारी' (Thicker) करें
        # वर्ड में 'wave' या 'double' बहुत पतली होने पर सादी काली लाइन जैसी लगती हैं
        if result['val'] in ['double', 'wave', 'dashDot'] and result['sz'] < 6:
            # कम से कम 0.75pt (6 units) सेट करें ताकि गैप और लहर साफ़ दिखे
            result['sz'] = 6 

        # 3. ✍️ IMPLICIT STYLE FIX: यदि मोटाई है पर स्टाइल नहीं (e.g. border: 1px red)
        # ब्राउज़र इसे 'solid' मानते हैं, वर्ड को भी यही बताएँ।
        elif result['sz'] > 0 and result['val'] == 'nil':
            result['val'] = 'single'

        return result