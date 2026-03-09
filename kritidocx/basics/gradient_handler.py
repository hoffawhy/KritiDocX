"""
GRADIENT HANDLER (The Color Blender)
------------------------------------
Responsibility:
Parses complex CSS 'linear-gradient' strings.
Since standard Word XML parsers struggle with complex CSS gradients, 
this module extracts the Primary Colors to ensure a valid fallback.

Logic:
1. Extract all colors from string like "linear-gradient(to right, red, yellow)".
2. Return the best single 'Solid' color representing the start of the gradient.
3. (Future Proofing) Return a config dict if we implement DrawingML Gradients later.
"""

import re
from kritidocx.basics.color_manager import ColorManager

class GradientHandler:
    
    # Regex to capture content inside parentheses of linear-gradient(...)
    _GRADIENT_PATTERN = re.compile(r'linear-gradient\((.*)\)', re.IGNORECASE)
    
    # Regex to split arguments by comma, ignoring commas inside rgb() parentheses
    # Logic: Match comma NOT followed by a closing parenthesis
    _SAFE_SPLIT = re.compile(r',(?![^()]*\))')

    @classmethod
    def parse_to_solid(cls, gradient_str):
        """
        Extracts the first valid color from a gradient string to use as Solid Fill.
        Returns: Hex String (RRGGBB) or None.
        """
        if not gradient_str or 'gradient' not in str(gradient_str):
            return None

        # 1. Extract content inside (...)
        match = cls._GRADIENT_PATTERN.search(gradient_str)
        if not match: 
            return None
        
        inner_content = match.group(1)
        
        # 2. Split parts (Direction vs Colors)
        parts = [p.strip() for p in cls._SAFE_SPLIT.split(inner_content)]
        
        # 3. Find first color
        # Parts look like: ['to right', '#FF0000', 'rgb(0,0,255)']
        for part in parts:
            # Skip directional keywords
            if part.startswith('to ') or 'deg' in part:
                continue
                
            # Attempt color parsing
            # First token in "red 50%" is "red"
            token = part.split()[0]
            
            # Use ColorManager to verify
            hex_val = ColorManager.get_hex(token)
            if hex_val:
                return hex_val
                
        return None  # Failed to extract