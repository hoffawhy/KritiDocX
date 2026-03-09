"""
COLOR MANAGER MODULE (The Visual Engine)
----------------------------------------
Responsibility: 
1. Convert any web color format (Name, RGB, RGBA, Hex) to clean 6-digit Hex.
2. Handle Transparency (Alpha Blending) for MS Word compatibility.
3. Validate against document theme.

Word Compatibility Note:
Word XML requires colors in 'RRGGBB' format (Uppercase, No Hash).
It strictly forbids RGBA or 3-digit Hex. This module ensures compliance.
"""

import re
import logging
from functools import lru_cache
from kritidocx.config.theme import ThemeConfig
from kritidocx.config.constants import DocConstants
import colorsys

logger = logging.getLogger("MyDocX_Engine")

class ColorManager:
    """
    Central logic for color manipulation.
    """

    # Default fallback color (Black)
    DEFAULT_HEX = "000000"
    # Background for blending transparency (Usually White page)
    BLEND_BACKGROUND_RGB = (255, 255, 255) 

    @staticmethod
    @lru_cache(maxsize=1024)
    def get_hex(color_input, default=None):
        """
        Main API: Converts input to MS Word compatible HEX string (e.g., 'FF0000').
        
        Args:
            color_input (str): 'red', '#FFF', 'rgb(0,0,0)', 'rgba(0,0,0,0.5)'
            default (str): Fallback if invalid.
            
        Returns:
            str: 6-char uppercase Hex string (or None/default).
        """
        if not color_input: 
            return default

        raw = str(color_input).strip().lower()

        # [IMPROVED]: Delegate to Gradient Handler
        if 'gradient' in raw:
            # Circular dependency prevention logic might be needed,
            # but simpler here since Handler imports ColorManager, we do Dynamic Import
            from kritidocx.basics.gradient_handler import GradientHandler
            return GradientHandler.parse_to_solid(raw)

        # [NEW FIX]: Background Shorthand Cleanup (Strip URL & Layout keywords)
        # Example: "url('img.png') no-repeat center #ffffff" -> "#ffffff"
        if 'url(' in raw or (len(raw.split()) > 1 and '#' in raw):
            # 1. Regex to remove url('...') parts completely
            # यह url() के अंदर की हर चीज़ को हटा देता है
            import re
            no_url_text = re.sub(r'url\s*\((?:[^)(]|\([^)(]*\))*\)', '', raw, flags=re.IGNORECASE)
            
            # 2. कॉमन लेआउट कीवर्ड्स की लिस्ट जिसे हम रंग नहीं मानेंगे
            ignored_keywords = [
                'none', 'repeat', 'no-repeat', 'repeat-x', 'repeat-y',
                'scroll', 'fixed', 'local',
                'center', 'top', 'bottom', 'left', 'right',
                'cover', 'contain', 'border-box', 'content-box', 'padding-box',
                '/', 'auto', 'important', '!important'
            ]
            
            # 3. स्ट्रिंग के टुकड़ों की जाँच करें
            tokens = no_url_text.split()
            found_color = None
            
            for token in tokens:
                token_clean = token.strip().lower()
                
                # यदि यह कीवर्ड है, तो छोड़ दें
                if token_clean in ignored_keywords or token_clean.endswith('%'):
                    continue
                
                # यदि इसमें '/' है (जैसे font-size 12px/20px), तो उसे छोड़ दें
                if '/' in token_clean:
                    continue
                
                # 4. इसे संभावित रंग मानें और टेस्ट करें
                # खुद को रिकर्सिव कॉल न करें ताकि अनंत लूप से बचा जा सके, 
                # इसके बजाय आंतरिक helpers को कॉल करें।
                
                # Check 1: HEX
                if token_clean.startswith('#'):
                    return ColorManager._clean_hex(token_clean)
                
                # Check 2: RGB/HSL
                if token_clean.startswith(('rgb', 'hsl')):
                    if 'hsl' in token_clean:
                        return ColorManager._parse_hsl_string(token_clean)
                    return ColorManager._parse_rgb_string(token_clean)
                
                # Check 3: Named Color
                if ColorManager._resolve_from_theme(token_clean):
                    found_color = ColorManager._clean_hex(ColorManager._resolve_from_theme(token_clean))
                    
            if found_color:
                return found_color
            
            # यदि सफाई के बाद भी कुछ नहीं मिला, तो सामान्य प्रवाह (Fallback) में जाने दें


        # 1. Check Magic Keywords
        if raw in ['auto', 'transparent', 'none', 'inherit', 'initial']:
            # Note: Word XML uses specific logic for these (handled in XmlFactory)
            # Returning None lets XML writer use its safe default.
            return None

        # 2. Check Config/Theme Map First (Fastest)
        # This checks ThemeConfig.COLOR_MAP and ThemeConfig.THEME_COLORS
        mapped_color = ColorManager._resolve_from_theme(raw)
        if mapped_color:
            return ColorManager._clean_hex(mapped_color)

        # 3. Check HEX Codes
        if raw.startswith('#'):
            return ColorManager._clean_hex(raw)

        # 4. Check RGB / RGBA Strings
        if raw.startswith('rgb'):
            return ColorManager._parse_rgb_string(raw)

        # [NEW] Check HSL / HSLA Strings (Modern Web Colors)
        if raw.startswith('hsl'):
            return ColorManager._parse_hsl_string(raw)

        # 5. [NEW FIX] Check Raw HEX (Missing '#', e.g. "00FF00" or "AAA")
        # Validate logic: Length 3, 6 or 8 AND all characters must be hex digits
        is_hex_chars = all(c in '0123456789abcdefABCDEF' for c in raw)
        if is_hex_chars and len(raw) in [3, 6, 8]:
            return ColorManager._clean_hex(raw)


        # 6. Invalid Color / Unknown Name
        logger.debug(f"🎨 Unknown color '{color_input}', falling back.")
        return default or ColorManager.DEFAULT_HEX

    # -------------------------------------------------------------------------
    # INTERNAL HELPERS (Hidden Mechanics)
    # -------------------------------------------------------------------------

    @staticmethod
    def _resolve_from_theme(name):
        """Checks Constants & Theme for color names."""
        
        # 1. First Priority: The Universal Standard (W3C CSS Colors)
        # अब यह सबसे पहले दुनिया के किसी भी स्टैंडर्ड वेब कलर को पहचानेगा।
        if name in DocConstants.WEB_COLORS:
            return DocConstants.WEB_COLORS[name]

        # 2. Second Priority: Theme Custom Override
        # यदि Theme में 'success_bg' जैसे custom नाम हैं, तो वो यहाँ मिलेंगे
        if name in ThemeConfig.THEME_COLORS:
            return ThemeConfig.THEME_COLORS[name]
            
        # 3. Third Priority: Basic Map Override
        # यदि आपने ThemeConfig में 'blue' के लिए कोई खास शेड (#2F5496) सेट किया है 
        # (Standard '0000FF' की जगह), तो वह यहाँ से मिलेगा।
        if name in ThemeConfig.COLOR_MAP:
            return ThemeConfig.COLOR_MAP[name]
            
        return None

    @staticmethod
    def _clean_hex(hex_str):
        """
        Sanitizes hex string.
        Input:  '#abc', '#FF0000', 'aabbcc'
        Output: 'AABBCC'
        """
        clean = hex_str.lstrip('#').upper()
        
        # Expand shorthand (#F00 -> #FF0000)
        if len(clean) == 3:
            clean = "".join([c*2 for c in clean])
            
        # Strict validation
        if len(clean) == 6 and all(c in '0123456789ABCDEF' for c in clean):
            return clean
            
        # If Hex is 8 digits (ARGB in some inputs), trim Alpha?
        # Word expects RRGGBB.
        if len(clean) == 8:
            # Assume AARRGGBB -> return RRGGBB
            return clean[2:]
            
        return ColorManager.DEFAULT_HEX

    @staticmethod
    def _parse_rgb_string(rgb_str):
        # Improved regex to handle decimal numbers and spaces safely
        pattern = r"rgba?\(\s*([\d\.]+)\s*,\s*([\d\.]+)\s*,\s*([\d\.]+)(?:\s*,\s*([\d\.]+))?\s*\)"
        match = re.search(pattern, rgb_str)
        if match:
            # values conversion to int safely
            r = int(float(match.group(1)))
            g = int(float(match.group(2)))
            b = int(float(match.group(3)))
            alpha = float(match.group(4)) if match.group(4) else 1.0
            
            if alpha < 1.0:
                r, g, b = ColorManager._blend_on_white(r, g, b, alpha)
            return '{:02X}{:02X}{:02X}'.format(r, g, b)
        return ColorManager.DEFAULT_HEX

    @staticmethod
    def _parse_hsl_string(hsl_str):
        # Support for floating numbers and percentages (100% or 100.5%)
        pattern = r"hsla?\(\s*([\d\.]+)\s*,\s*([\d\.]+)%\s*,\s*([\d\.]+)%(?:\s*,\s*([\d\.]+))?\s*\)"
        match = re.search(pattern, hsl_str)
        if match:
            h = (float(match.group(1)) % 360) / 360.0
            s = float(match.group(2)) / 100.0
            l = float(match.group(3)) / 100.0
            alpha = float(match.group(4)) if match.group(4) else 1.0
            
            r_f, g_f, b_f = colorsys.hls_to_rgb(h, l, s)
            r, g, b = int(r_f*255), int(g_f*255), int(b_f*255)
            
            if alpha < 1.0:
                r, g, b = ColorManager._blend_on_white(r, g, b, alpha)
            return '{:02X}{:02X}{:02X}'.format(r, g, b)
        return ColorManager.DEFAULT_HEX

    @staticmethod
    def _blend_on_white(r, g, b, alpha):
        """
        Formula to flatten RGBA onto White background.
        Visual Approximation logic.
        """
        bg_r, bg_g, bg_b = ColorManager.BLEND_BACKGROUND_RGB
        
        new_r = int(r * alpha + bg_r * (1 - alpha))
        new_g = int(g * alpha + bg_g * (1 - alpha))
        new_b = int(b * alpha + bg_b * (1 - alpha))
        
        return new_r, new_g, new_b


    def _parse_hsl_string(hsl_str):
        # Support for floating numbers and percentages (100% or 100.5%)
        pattern = r"hsla?\(\s*([\d\.]+)\s*,\s*([\d\.]+)%\s*,\s*([\d\.]+)%(?:\s*,\s*([\d\.]+))?\s*\)"
        match = re.search(pattern, hsl_str)
        if match:
            h = (float(match.group(1)) % 360) / 360.0
            s = float(match.group(2)) / 100.0
            l = float(match.group(3)) / 100.0
            alpha = float(match.group(4)) if match.group(4) else 1.0
            
            r_f, g_f, b_f = colorsys.hls_to_rgb(h, l, s)
            r, g, b = int(r_f*255), int(g_f*255), int(b_f*255)
            
            if alpha < 1.0:
                r, g, b = ColorManager._blend_on_white(r, g, b, alpha)
            return '{:02X}{:02X}{:02X}'.format(r, g, b)
        return ColorManager.DEFAULT_HEX


    @staticmethod
    def get_rgb_tuple(hex_str):
        """
        Optional helper: Returns (255, 0, 0) tuple for logic needing direct values
        (e.g., Image Generation libraries).
        """
        clean = ColorManager.get_hex(hex_str) or "000000"
        return tuple(int(clean[i:i+2], 16) for i in (0, 2, 4))