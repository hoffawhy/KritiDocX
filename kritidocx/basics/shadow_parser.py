"""
from kritidocx.utils.logger import logger
SHADOW PARSER (The 3D Architect)
--------------------------------
Responsibility: Parses CSS box-shadow into Word XML effect properties.
Target Logic:
    CSS: Offset X, Offset Y, Blur, Color.
    Word: Distance (dist), Angle (dir), BlurRad, Color.

Math: Converts Cartesian coordinates (x,y) to Polar coordinates (r, theta) for Word.
"""

import re
import math
from kritidocx.config.settings import AppConfig
from kritidocx.basics.unit_converter import UnitConverter
from kritidocx.basics.color_manager import ColorManager
from kritidocx.utils import logger

class ShadowParser:
    @staticmethod
    def parse(shadow_str):
        """
        Input: '10px 10px 5px gray'
        Output: { 'dist': 127000, 'dir': 2700000, 'blur': 63500, 'color': '808080' }
        """
        if not shadow_str or shadow_str == 'none':
            return None

        # 1. Regex to split (matches X, Y, [Blur], [Color])
        # Note: Handling CSS units safely
        pattern = r"(-?[\d\.]+[a-z%]*)\s+(-?[\d\.]+[a-z%]*)(?:\s+(-?[\d\.]+[a-z%]*))?\s*(.*)?"
        match = re.search(pattern, shadow_str.strip())
        
        if not match:
            return None

        # 2. Extract Components
        off_x_str = match.group(1) # Horizontal Offset
        off_y_str = match.group(2) # Vertical Offset
        blur_str = match.group(3)  # Blur (Optional)
        color_str = match.group(4) # Color (Optional)

        # 3. Calculate Physics (Pixels -> EMUs)
        # 1px = 9525 EMUs (approx 12700 if 72dpi, standardized here)
        from kritidocx.config.constants import DocConstants
        
        # Word DrawingML needs strict EMUs
        x = UnitConverter.to_emus(off_x_str)
        y = UnitConverter.to_emus(off_y_str)
        blur = UnitConverter.to_emus(blur_str) if blur_str else 0

        # 4. Math: Cartesian (x,y) -> Polar (dist, angle)
        # Distance (Hypotenuse)
        dist = int(math.sqrt(x*x + y*y))
        
        # Direction (Angle) - Word 0 deg = Right, 90 deg = Down
        # Math atan2 returns radians from X axis.
        angle_rad = math.atan2(y, x)
        angle_deg = math.degrees(angle_rad)
        
        # Normalize (Word uses positive integers 0-360)
        if angle_deg < 0:
            angle_deg += 360
            
        # Word stores angle in 60000ths of a degree (270 deg = 16,200,000)
        final_dir = int(angle_deg * 60000)

        # 5. Color Resolution
        hex_color = ColorManager.get_hex(color_str) if color_str else "000000"
        
        # शैडो थोड़ी ट्रांसपेरेंट अच्छी लगती है (Default 50-60% opacity look simulation via color?)
        # अभी के लिए सॉलिड कलर वापस कर रहे हैं। XML बिल्डर में अल्फा जोड़ सकते हैं।


        if getattr(AppConfig, 'DEBUG_TEXT_LAYOUT', False):
            logger.debug(f"   📐 [ShadowParser] CSS: '{shadow_str}' -> Word EMUs: dist={dist}, dir={final_dir}, blur={blur}, col={hex_color}")
        

        return {
            'type': 'outerShdw', # Outer Shadow Standard
            'dist': dist,        # EMUs
            'dir': final_dir,    # Angle Units
            'blurRad': blur,     # EMUs
            'color': hex_color
        }