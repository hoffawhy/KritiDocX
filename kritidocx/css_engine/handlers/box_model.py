"""
BOX MODEL HANDLER
-----------------
Handles expansion of CSS Spacing properties.
Converts shorthands into explicit directional properties.
"""

class BoxModelHandler:
    @staticmethod
    def process(prop, value, attributes_dict):
        """
        Input: prop='margin', value='10px 5px'
        Modifies attributes_dict in-place to add:
        {'margin-top': '10px', 'margin-right': '5px', ...}
        """
        # यदि value खाली है तो कुछ न करें
        if not value: return

        parts = value.strip().split()
        count = len(parts)
        
        # बेस वेरिएबल्स
        top = right = bottom = left = None
        
        # CSS Expansion Logic (Standard)
        if count == 1:
            # margin: 10px; -> all sides
            top = right = bottom = left = parts[0]
        elif count == 2:
            # margin: 10px 20px; -> top/bottom=10, right/left=20
            top = bottom = parts[0]
            right = left = parts[1]
        elif count == 3:
            # margin: 10px 5px 20px; -> top=10, horizontal=5, bottom=20
            top = parts[0]
            right = left = parts[1]
            bottom = parts[2]
        elif count >= 4:
            # margin: 10px 20px 30px 40px; -> top right bottom left (Clockwise)
            top = parts[0]
            right = parts[1]
            bottom = parts[2]
            left = parts[3]
            
        # डिक्शनरी में जोड़ें (मूल कुंजी 'margin' को हटाया नहीं जाता, ताकि reference बना रहे)
        if top:
            attributes_dict[f"{prop}-top"] = top
            attributes_dict[f"{prop}-right"] = right
            attributes_dict[f"{prop}-bottom"] = bottom
            attributes_dict[f"{prop}-left"] = left