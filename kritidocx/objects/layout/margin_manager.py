"""
MARGIN MANAGER (The Boundary Guardian)
--------------------------------------
Responsibility:
Manages page boundaries (Margins), Gutter (Binding space), and Header/Footer distances.

Features:
1. Universal Inputs: Accepts CSS logic ('1in', '2.54cm', '96px') or Raw values.
2. Preset Library: Supports Word's standard presets (Normal, Narrow, Wide).
3. Binding Support: Handles 'Gutter' for physical printing.
4. Book Mode: Supports 'Mirror Margins' (Left/Right becomes Inside/Outside).

Dependency:
- Uses 'UnitConverter' to convert everything to 'Twips'.
  (Twips is the native unit for Layouts in Word. 1440 Twips = 1 Inch).
"""

from docx.shared import Twips
import logging
from kritidocx.basics.unit_converter import UnitConverter

logger = logging.getLogger("MyDocX_Engine")

class MarginManager:
    """
    Advanced controller for Document Margins.
    Operates on a python-docx 'Section' object.
    """

    # Standard Word Presets (Values in Inches)
    PRESETS = {
        'normal':   {'top': 1,   'bottom': 1,   'left': 1,    'right': 1},
        'narrow':   {'top': 0.5, 'bottom': 0.5, 'left': 0.5,  'right': 0.5},
        'moderate': {'top': 1,   'bottom': 1,   'left': 0.75, 'right': 0.75},
        'wide':     {'top': 1,   'bottom': 1,   'left': 2,    'right': 2},
        'mirrored': {'top': 1,   'bottom': 1,   'inside': 1.25, 'outside': 1}, # Special Case
    }

    # Aliases mapping (CSS keys -> Word keys)
    KEY_MAP = {
        # Top
        'top': 'top', 'margin-top': 'top', 'margin_top': 'top', 'padding-top': 'top',
        # Bottom
        'bottom': 'bottom', 'margin-bottom': 'bottom', 'margin_bottom': 'bottom', 'padding-bottom': 'bottom',
        # Left (or Inside)
        'left': 'left', 'margin-left': 'left', 'margin_left': 'left', 'padding-left': 'left', 'inside': 'left',
        # Right (or Outside)
        'right': 'right', 'margin-right': 'right', 'margin_right': 'right', 'padding-right': 'right', 'outside': 'right',
        # Header/Footer Distance
        'header': 'header', 'header_dist': 'header',
        'footer': 'footer', 'footer_dist': 'footer',
        # Gutter (Binding)
        'gutter': 'gutter', 'binding': 'gutter'
    }

    def __init__(self, doc):
        self.doc = doc

    # =========================================================================
    # 1. 🏗️ CORE APPLY METHODS
    # =========================================================================

    def apply_margins(self, section, style_data=None, preset_name=None, gutter=None, mirror_margins=False):
        """
        Master method to apply margins.
        Priority: Explicit style_data > Preset > Defaults.
        
        Args:
            section: The target python-docx Section object.
            style_data (dict): e.g., {'top': '2cm', 'left': '1in'}
            preset_name (str): 'normal', 'narrow', etc.
            gutter (str/int): '0.5in' (Extra space for binding)
            mirror_margins (bool): If True, Left becomes Inside, Right becomes Outside.
        """
        
        # 1. Start with Default/Current values or Preset
        final_values = {}
        
        if preset_name and preset_name in self.PRESETS:
            # Load preset (Convert Inches to string for consistency)
            for k, v in self.PRESETS[preset_name].items():
                final_values[k] = f"{v}in"
            
            # Special Handling for 'Mirrored' preset flag
            if preset_name == 'mirrored':
                mirror_margins = True

        # 2. Overlay Custom Styles
        if style_data:
            for raw_k, raw_v in style_data.items():
                normalized_key = self.KEY_MAP.get(raw_k.lower())
                if normalized_key:
                    final_values[normalized_key] = raw_v

        # 3. Apply Binding Gutter
        if gutter:
            final_values['gutter'] = gutter

        # 4. Apply to Section Object
        self._inject_into_section(section, final_values, mirror_margins)

    def _inject_into_section(self, section, values_map, mirror_flag):
        """Internal helper: Converts units and assigns to docx section properties."""
        
        def _set_prop(attr_name, val_str):
            if val_str is None: return
            
            # Convert anything to Twips (Integer)
            twips = UnitConverter.to_twips(val_str)
            if twips is not None:
                try:
                    # python-docx requires explicit Length objects like Twips/Inches
                    # Setting simple int sometimes works, but Twips() wrapper is safer type-wise
                    setattr(section, attr_name, Twips(twips))
                except Exception as e:
                    logger.warning(f"Failed to set margin '{attr_name}': {e}")

        # --- A. Standard Margins ---
        _set_prop('top_margin', values_map.get('top'))
        _set_prop('bottom_margin', values_map.get('bottom'))
        _set_prop('left_margin', values_map.get('left'))
        _set_prop('right_margin', values_map.get('right'))
        
        # --- B. Special Layouts ---
        _set_prop('gutter', values_map.get('gutter'))
        
        _set_prop('header_distance', values_map.get('header'))
        _set_prop('footer_distance', values_map.get('footer'))

        # --- C. Mirror Margins (Book Mode) ---
        if mirror_flag:
            # Word switches Left/Right logic internally to Inside/Outside
            section.mirror_margins = True
            
            # If user provided 'inside'/'outside' keys manually in styles, they override left/right
            if values_map.get('inside'):
                _set_prop('left_margin', values_map.get('inside')) # Internal map Left=Inside
            if values_map.get('outside'):
                _set_prop('right_margin', values_map.get('outside')) # Internal map Right=Outside
        else:
            section.mirror_margins = False

    # =========================================================================
    # 2. ⚡ UTILITY / SHORTCUTS
    # =========================================================================

    def apply_preset(self, section, name):
        """Shortcut for simple preset application."""
        self.apply_margins(section, preset_name=name)

    @staticmethod
    def get_printable_width(section):
        """
        Calculates available width for content (Page Width - Margins).
        Useful for Table Autofit calculations.
        Returns: Twips (int)
        """
        try:
            page_w = section.page_width
            # Handle possible None types in python-docx properties
            left = section.left_margin or Twips(0)
            right = section.right_margin or Twips(0)
            gutter = section.gutter or Twips(0)
            
            # Formula: Page - (Left + Right + Gutter)
            available = page_w - left - right - gutter
            return available
        except:
            # Fallback A4 standard usable width (approx 6 inches)
            return 8640 # ~6 inch in twips