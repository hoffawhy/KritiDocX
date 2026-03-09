"""
SHAPE FACTORY (The Vector Artist)
---------------------------------
Responsibility:
Interprets visual properties for Textboxes and Shapes.
Converts high-level Styles into Low-level DrawingML definitions.

Scopes handled:
1. Fill: Solid Color, None (Transparent).
2. Stroke (Line): Color, Weight (Thickness), Dash Style.
3. Geometry: Shape presets (Rect).
4. Textbox Body: Internal margins (Padding).

Mathematical Conversion:
Border widths in Word DrawingML uses EMUs (different from Tables/Paragraphs).
1 pt = 12700 EMU.
"""

from kritidocx.basics.color_manager import ColorManager
from kritidocx.basics.unit_converter import UnitConverter
from kritidocx.basics.border_parser import BorderParser
from kritidocx.basics.css_parser import CssParser

class ShapeFactory:
    """
    Translates styles into configuration dicts for XML Builder (wps:spPr).
    """

    # Mapping CSS border styles to Word DrawingML 'prstDash' values
    DASH_MAP = {
        'solid': 'solid',
        'dotted': 'sysDot',        # Square dots
        'dashed': 'dash',          # Regular dashes
        'double': 'solid',         # DrawingML handles double via cmpdLine (not simple prst), fallback solid
        'groove': 'solid',         # Fallback
        'ridge': 'solid',          # Fallback
        'inset': 'solid',          # Fallback
        'outset': 'solid'          # Fallback
    }

    # Standard Internal Margins (Padding) if not specified - ~0.1 inch
    DEFAULT_PADDING = "91440" # 91440 EMUs = 0.1 inch

    @staticmethod
    def create_shape_config(style_data, shape_type='rect'):
        """
        [ENGINE UPGRADE]: Generates configuration dict for DrawingXML.
        """
        if style_data is None: 
            style_data = {}

        config = {
            'geom': shape_type,
            'fill': None,
            'outline': None,
            'padding': None,
            'shadow': None
        }

        # 1. Fill Logic (Background) -> Handles Transparent/Solid
        config['fill'] = ShapeFactory._resolve_fill(style_data)

        # 2. Outline Logic (Border) -> Handles Dash/Thickness
        config['outline'] = ShapeFactory._resolve_outline(style_data)

        # 3. Padding Logic (Internal Margins)
        config['padding'] = ShapeFactory._resolve_padding(style_data)

        # 4. Shadow Logic [NEW BLOCK]
        config['shadow'] = ShapeFactory._resolve_shadow(style_data)


        return config

    # =========================================================================
    # 🕵️ INTERNAL RESOLVERS
    # =========================================================================

    @staticmethod
    def _resolve_fill(style_data):
        """Determines background color."""
        bg = style_data.get('background-color') or style_data.get('background')
        
        # Transparent logic
        if not bg or bg == 'transparent' or bg == 'none':
            return {'type': 'noFill'}
        
        # Color logic
        hex_val = ColorManager.get_hex(bg)
        if hex_val:
            return {'type': 'solid', 'color': hex_val}
            
        return {'type': 'noFill'} # Default fallthrough

    @staticmethod
    def _resolve_outline(style_data):
        """
        [MATH FIX]: Converts Table Borders (Eighths) to Shape Outlines (EMUs).
        Detects dashed/dotted styles properly.
        """
        # 1. प्राथमिकता 1: ग्लोबल बॉर्डर (border: ...)
        border_str = style_data.get('border')
        
        # 2. प्राथमिकता 2: यदि ग्लोबल नहीं है, तो साइड स्पेसिफिक बॉर्डर ढूँढें
        # (नोट: Word Shapes में केवल एक ही आउटलाइन होती है जो चारों तरफ लगती है।
        # इसलिए हम किसी भी एक साइड का स्टाइल उठा कर शेप पर लगा देंगे)
        if not border_str:
            for side in ['right', 'left', 'bottom', 'top']:
                val = style_data.get(f'border-{side}')
                # वैलिडिटी चेक
                if val and val != 'none' and '0px' not in str(val):
                    border_str = val
                    break

        # '0px' or 'none' means invisible line
        if not border_str or border_str == 'none' or '0px' in border_str:
            return {'type': 'noFill'} 

        # 1. Parse using existing BorderParser
        # (यह '1px dashed red' को {sz: 8, val: 'dashed', color: 'FF0000'} में बदलता है)
        b_props = BorderParser.parse(border_str)
        if not b_props: return {'type': 'noFill'}

        # 2. UNIT CONVERSION: Eighths (1/8pt) -> EMUs
        # Formula: 1pt = 12700 EMUs. 1/8pt = 12700/8 = 1587.5 EMUs
        sz_eighths = b_props.get('sz', 4)
        width_emu = int(sz_eighths * 1587.5)
        
        # Safety: Ensure min visibility (0.5pt = 6350)
        width_emu = max(6350, width_emu) 

        # 3. Resolve Dash Style
        val_raw = b_props.get('val', 'single').lower()
        dash_val = ShapeFactory.DASH_MAP.get(val_raw, 'solid')

        # 4. Color Check
        col_hex = b_props.get('color', '000000')
        if col_hex == 'auto': col_hex = '000000'

        return {
            'type': 'solid',
            'w': width_emu,
            'color': col_hex,
            'dash': dash_val
        }

    @staticmethod
    def _resolve_padding(style_data):
        """
        Converts CSS padding to Shape Insets (lIns, tIns...).
        Word XML expects EMUs for these values.
        """
        # We need expansion logic if shorthand used (already done by CssParser in most cases, 
        # but let's be safe using explicit lookups).
        
        # Helper to get EMU
        def get_emu(key, default_emu):
            val = style_data.get(key)
            if val:
                return str(UnitConverter.to_emus(val))
            return default_emu

        # CSS 'padding' often sets default spacing for text inside box
        # Defaults to ~0.1 inch if not specified to allow text breathing room
        l = get_emu('padding-left', ShapeFactory.DEFAULT_PADDING)
        t = get_emu('padding-top', str(int(int(ShapeFactory.DEFAULT_PADDING)/2))) # Top padding slightly less by default visually
        r = get_emu('padding-right', ShapeFactory.DEFAULT_PADDING)
        b = get_emu('padding-bottom', str(int(int(ShapeFactory.DEFAULT_PADDING)/2)))

        return {
            'lIns': l,
            'tIns': t,
            'rIns': r,
            'bIns': b
        }
        
     
    @staticmethod
    def _resolve_shadow(style_data):
        """Parsing box-shadow for 3D effect."""
        raw_shadow = style_data.get('box-shadow') or style_data.get('box_shadow')
        if not raw_shadow or raw_shadow == 'none':
            return None
            
        from kritidocx.basics.shadow_parser import ShadowParser
        return ShadowParser.parse(raw_shadow)    