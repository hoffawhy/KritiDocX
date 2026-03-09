"""
DIMENSIONS HANDLER
------------------
Handles Width, Height, and Transforms (Rotation).
Normalizes unit-less numbers to 'px'.
"""
import re

class DimensionHandler:
    @staticmethod
    def process(prop, value, attributes_dict):
        clean_val = value.strip().lower()
        
        # 1. Transform / Rotation Logic (CRITICAL FIX)
        # Matches: transform: rotate(15deg); or rotate(-15deg)
        if prop == 'transform':
            match = re.search(r'rotate\s*\(\s*(-?[\d\.]+)\s*deg\s*\)', clean_val)
            if match:
                # We store a purely numeric float key for the logic engine
                attributes_dict['rotation_deg'] = float(match.group(1))
            return

        # 2. Position Coordinates (Left/Top/Right/Bottom)
        if prop in ['left', 'top', 'right', 'bottom']:
            attributes_dict[prop] = clean_val
            return

        # 3. Z-Index (Stacking)
        if prop == 'z-index':
            if clean_val.lstrip('-').isdigit():
                attributes_dict['z_index'] = int(clean_val)
            return

        # 4. Standard Dimensions (Width/Height)
        attributes_dict[prop] = clean_val