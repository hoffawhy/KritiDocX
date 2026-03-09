"""
UNIT CONVERTER MODULE (The Physics Engine)
------------------------------------------
जिम्मेदारी: CSS/HTML यूनिट्स (px, pt, cm, in, %, em) को Word OOXML यूनिट्स में बदलना।

यह मॉड्यूल 'DocConstants' (Physics) और इनपुट डेटा के बीच का पुल (Bridge) है।
इसमें 'Memoization' (Caching) का उपयोग किया गया है ताकि बार-बार गणना न करनी पड़े।
"""

import re
import logging
from functools import lru_cache
from kritidocx.config.constants import DocConstants

logger = logging.getLogger("MyDocX_Engine")

class UnitConverter:
    """
    Central logic for dimension conversion.
    Safe-guarded against NoneTypes and invalid strings.
    """

    # बेस फ़ॉन्ट साइज़ (Points) - 'em' और 'rem' की गणना के लिए
    BASE_FONT_SIZE_PT = 11  # e.g. 1em = 11pt = 220 Twips

    @staticmethod
    @lru_cache(maxsize=4096)
    def parse_value_string(val_str):
        """
        Extracts number and unit from strings like '10px', '2.5in', '-5pt'.
        
        Returns:
            (float_value, unit_string) OR (None, None) if invalid.
        """
        if not val_str: 
            return 0.0, None
        
        s = str(val_str).strip().lower()
        
        # 1. Handle Keywords
        if s in ['auto', 'initial', 'inherit', 'none', 'normal']:
            return 0.0, 'keyword'


        # [CORRECTED CODE BLOCK]
        # [NEW FIX]: 'Calc' Function Handling (Crash Prevention)
        # Strategy: Simplification. "calc(100% - 20px)" -> "100%"
        if 'calc' in s:
            try:
                # 1. 'calc' के बाद का पहला साफ़ नंबर+यूनिट ढूँढें
                # Regex: कोष्ठक के अंदर पहली संख्या (integer/float) और उसका यूनिट पकड़ें
                calc_match = re.search(r'calc\s*\(\s*([-\+]?[\d\.]+)([a-z%]*)', s)
                
                if calc_match:
                    # साफ़ वैल्यू बनाएँ (e.g. "100" + "%")
                    clean_extracted = calc_match.group(1) + calc_match.group(2)
                    
                    # CORRECTION HERE: 'cls' की जगह Class Name का उपयोग करें
                    return UnitConverter.parse_value_string(clean_extracted)
            except Exception:
                # यदि रेगेक्स फेल हो जाए
                pass
            return 0.0, 'px'

        # 2. Extract using Regex
        # Matches: Optional minus, Integers/Floats, Optional Unit
        match = re.match(r"^(-?[\d\.]+)([a-z%]*)$", s)
        
        if match:
            try:
                number = float(match.group(1))
                unit = match.group(2) if match.group(2) else 'px' # Default to px if missing
                return number, unit
            except ValueError:
                pass
        
        return 0.0, 'px'  # Fail safe

    # =========================================================================
    # 1. TWIPS CONVERTER (For Paragraphs, Indentation, Cell Margins)
    # Target: 1/1440 Inch
    # =========================================================================
    @classmethod
    def to_twips(cls, val_str, default=0):
        val, unit = cls.parse_value_string(val_str)
        if val is None or unit == 'keyword' or val == 0: 
            return default

        result = 0.0
        
        if unit == 'in':   result = val * DocConstants.TWIPS_PER_INCH
        elif unit == 'pt': result = val * DocConstants.TWIPS_PER_POINT
        elif unit == 'px': result = val * DocConstants.TWIPS_PER_PIXEL
        elif unit == 'cm': result = val * DocConstants.TWIPS_PER_CM
        elif unit == 'mm': result = val * DocConstants.TWIPS_PER_MM
        
        # Relative Text Units (Font Based)
        elif unit in ['em', 'rem']:
            # 1em = 11pt * 20 = 220 Twips
            result = val * cls.BASE_FONT_SIZE_PT * DocConstants.TWIPS_PER_POINT
        
        elif unit in ['ch', 'ex']:
            # 1ch (0 character width) approx 0.55em - 0.6em depending on font.
            # 1ex (x-height) is roughly 0.5em.
            # Safe Fallback: 0.55 * Font Size
            factor = 0.55
            result = val * (cls.BASE_FONT_SIZE_PT * factor) * DocConstants.TWIPS_PER_POINT

        # Viewport Units (Page Based - Standard A4 approx estimates)
        # Note: Document Viewport is static paper size, not screen.
        elif unit == 'vw':
            # A4 Width (11906 Twips) / 100 ≈ 119 Twips
            result = val * 119
        elif unit == 'vh':
            # A4 Height (16838 Twips) / 100 ≈ 168 Twips
            result = val * 168
        elif unit == 'vmin':
            result = val * 119 # Smaller of vw/vh
        elif unit == 'vmax':
            result = val * 168 # Larger of vw/vh

        # Print Units
        elif unit == 'pc': # Picas (1pc = 12pt)
            result = val * 12 * DocConstants.TWIPS_PER_POINT
            
        else:
            # Fallback assume PX (standard browser behavior)
            result = val * DocConstants.TWIPS_PER_PIXEL

        return int(round(result))

    # =========================================================================
    # 2. EMUS CONVERTER (For Images, Shapes, Canvases)
    # Target: 1/914400 Inch (High Precision)
    # =========================================================================
    @classmethod
    def to_emus(cls, val_str, default=0):
        val, unit = cls.parse_value_string(val_str)
        if unit == 'keyword' or val == 0: return default

        result = 0.0

        if unit == 'in':   result = val * DocConstants.EMU_PER_INCH
        elif unit == 'cm': result = val * DocConstants.EMU_PER_CM
        elif unit == 'mm': result = val * DocConstants.EMU_PER_MM
        elif unit == 'pt': result = val * DocConstants.EMU_PER_POINT
        elif unit == 'px': result = val * DocConstants.EMU_PER_PIXEL
        
        else:
            # Fallback assume PX (standard for web images)
            result = val * DocConstants.EMU_PER_PIXEL

        return int(round(result))

    # =========================================================================
    # 3. FONT SIZE CONVERTER (For Text Runs)
    # Target: Half-Points (1/144 Inch)
    # Example: 12pt -> 24 half-points
    # =========================================================================
    @classmethod
    def to_half_points(cls, val_str, default=22): # Default 11pt -> 22
        val, unit = cls.parse_value_string(val_str)
        if val == 0: return default

        points = 0.0
        
        if unit == 'pt':   points = val
        elif unit == 'px': points = val * 0.75
        elif unit == 'in': points = val * 72
        
        # [IMPROVED]: Comprehensive Relative Unit Support
        elif unit in ['em', 'rem']: 
            points = val * cls.BASE_FONT_SIZE_PT
        
        elif unit == 'pc': # 1 Pica = 12 Points
            points = val * 12
            
        elif unit in ['ch', 'ex']:
            # 'ch' is mostly width, but if used in size context (rare), treat like 0.5em
            points = val * (cls.BASE_FONT_SIZE_PT * 0.55)
            
        elif unit == '%':  
            points = (val / 100.0) * cls.BASE_FONT_SIZE_PT
            
        elif unit in ['vw', 'vh']:
            # Viewport fonts: e.g. "5vw". On paper ~6inch width: 5% of 6inch
            # 6 inches = 432 pt. 1vw = 4.32pt.
            base_viewport_pt = 432 # Avg writable width points
            points = val * (base_viewport_pt / 100.0)
            
        else:              
            points = val

        # Word wants Half-Points (integer)
        return int(round(points * 2))

    # =========================================================================
    # 4. BORDER SIZE CONVERTER (For Table/Paragraph Borders)
    # Target: Eighths of a Point (1/576 Inch)
    # Example: 1px (~0.75pt) -> 6 eighths
    # =========================================================================
    @classmethod
    def to_border_eighths(cls, val_str):
        # [FIX START] Handle text keywords explicitly BEFORE parsing number
        # because "thin" parses to 0.0, which triggered the exit guard too early.
        if not val_str: return 0
        s_raw = str(val_str).lower().strip()
        
        if 'thin' in s_raw: return 4
        if 'medium' in s_raw: return 12
        if 'thick' in s_raw: return 24
        # [FIX END]

        val, unit = cls.parse_value_string(val_str)
        if val == 0: return 0

        points = 0.0
        if unit == 'pt':   points = val
        elif unit == 'px': points = val * 0.75
        # Fallbacks managed above, keeping numerical calculation clean
        else: points = 0.5 # Minimum logic if unit weird but val > 0

        # Minimum visibility rule:
        # Word min border size is 1/4 pt (2 eighths) or 1/8 pt (1 eighth).
        # We ensure visible lines don't vanish.
        eighths = int(round(points * 8))
        return max(2, eighths) # Min 0.25pt visibility

    # =========================================================================
    # 5. TABLE PERCENTAGE WIDTH (Fixed for all units including 'ch')
    # Target: Fiftieths of a percent (e.g. 100% = 5000 units)
    # =========================================================================
    @classmethod
    def to_table_pct(cls, val_str):
        """
        Strict Percentage Converter. 
        Note: Fixed units (px/ch) logic is now moved to PropsManager to use 'dxa' instead.
        """
        val, unit = cls.parse_value_string(val_str)
        if val == 0: return 5000
        
        if unit == '%':
            pct_unit = int(val * 50)
            return min(pct_unit, 5000)
            
        # Fallback only
        return 5000