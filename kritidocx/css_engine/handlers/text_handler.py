"""
from kritidocx.utils.logger import logger
TEXT HANDLER (The Typographer)
------------------------------
Responsible for normalization of Font and Text Decoration rules.
Features:
1. Advanced Text-Decoration Parsing: Extracts color and style ('underline wavy blue').
2. Font Family Cleanup: Removes quotes/whitespace from family lists.
3. Alignment Normalization: Maps synonyms.
"""

from kritidocx.config.settings import AppConfig
from kritidocx.basics.color_manager import ColorManager
from kritidocx.utils import logger

class TextHandler:
    
    # Allowed Underline Styles for Word
    UNDERLINE_STYLES = [
        'single', 'double', 'dotted', 'dashed', 'wave', 'thick'
    ]
    
    # CSS -> Word mapping for specific underline keywords
    DECORATION_MAP = {
        'wavy': 'wave', # Critical mapping
        'solid': 'single',
        'underline': 'single' # Default keyword acts as trigger
    }

    @staticmethod
    def process(prop, value, attributes_dict):
        """
        Input: prop='text-decoration', value='underline wavy #0000FF'
        Output: Updates dict with specific styling keys suitable for Objects.
        """
        val = str(value).lower().strip()
        
        # 1. TEXT DECORATION (Underline / Strikethrough)
        # Complex logic: can contain "underline", "line-through", style, color.
        if prop == 'text-decoration':
            TextHandler._parse_decoration(val, attributes_dict)
            # मूल स्ट्रिंग भी रखें ताकि कोई कस्टम लॉजिक छूटे नहीं
            attributes_dict['text-decoration'] = value
            return

        # Example: "bold 12px/20px Arial, sans-serif"
        if prop == 'font':
            TextHandler._expand_font_shorthand(value, attributes_dict)
            return

        # 2. FONT FAMILY
        # Cleans: "'Times New Roman', serif" -> "Times New Roman"
        if prop == 'font-family':
            attributes_dict[prop] = TextHandler._clean_font_family(value)
            return

        # 3. TEXT ALIGNMENT
        if prop == 'text-align' or prop == 'align':
            # Map HTML 'middle' to standard 'center' just in case
            if 'middle' in val or 'center' in val:
                attributes_dict['text-align'] = 'center'
            else:
                attributes_dict['text-align'] = val
            return

        # 4. FONT WEIGHT (Bold)
        if prop == 'font-weight':
            # 'bold', 'bolder', '700', '800' -> True
            is_bold = ('bold' in val) or (val.isdigit() and int(val) >= 700)
            attributes_dict['bold'] = is_bold
            attributes_dict['font-weight'] = value
            return

        # 5. FONT STYLE (Italic)
        if prop == 'font-style':
            is_italic = ('italic' in val or 'oblique' in val)
            attributes_dict['italic'] = is_italic
            attributes_dict['font-style'] = value
            return

        # 6. COLORS (Direct mapping)
        if prop == 'color':
            hex_code = ColorManager.get_hex(value)
            if hex_code:
                attributes_dict['color'] = hex_code
            return
        
        # 7. TEXT SHADOW (Connects to ShadowParser)
        if prop == 'text-shadow':
            from kritidocx.basics.shadow_parser import ShadowParser
            shadow_data = ShadowParser.parse(val)
            if getattr(AppConfig, 'DEBUG_TEXT_LAYOUT', False):
                 logger.debug(f"   🏷️ [TextHandler] Found text-shadow! Data Extracted: {'YES' if shadow_data else 'NO'}")
            if shadow_data:
                # हम डिक्शनरी को सेव करेंगे ताकि RunManager उसे पढ़ सके
                attributes_dict['shadow_dict'] = shadow_data
                attributes_dict['shadow'] = True # Trigger for basic checks
            return


        # 8. TEXT GLOW (e.g. text-glow: 5px red)
        if prop == 'text-glow':
            parts = val.split()
            if len(parts) >= 2:
                from kritidocx.basics.unit_converter import UnitConverter
                attributes_dict['glow_dict'] = {
                    'rad': UnitConverter.to_emus(parts[0]), # 5px to EMUs
                    'color': ColorManager.get_hex(parts[1])
                }
            return

        # 9. TEXT OUTLINE (e.g. text-outline: 1px blue)
        if prop == 'text-outline':
            parts = val.split()
            if len(parts) >= 2:
                from kritidocx.basics.unit_converter import UnitConverter
                attributes_dict['outline_dict'] = {
                    'w': UnitConverter.to_emus(parts[0]), # width in EMUs
                    'color': ColorManager.get_hex(parts[1])
                }
            return

        #10. TEXT REFLECTION (प्रीमियम सुधार - अब वर्ड XML स्केल के अनुसार)
        # CSS उदाहरण: '5px 60%' (दूरी 5px, शुरूआती दृश्यता 60%)
        if prop == 'text-reflection':
            parts = val.split()
            if len(parts) >= 1:
                from kritidocx.basics.unit_converter import UnitConverter
                
                # 1. दूरी (Distance): वर्ड EMUs में बदलेगा
                dist = UnitConverter.to_emus(parts[0])
                
                # 2. दृश्यता/ओपेसिटी (Alpha): 
                # वर्ड में 100% = 100000 होता है।
                # आपके मैन्युअल XML के अनुसार 60% = 60000 सबसे बेहतर दिखता है।
                alpha = 60000 # डिफ़ॉल्ट 60%
                
                if len(parts) > 1:
                    alpha_str = parts[1].replace('%', '')
                    try:
                        alpha_val = float(alpha_str)
                        # यदि यूजर '0.6' लिखे या '60%', दोनों को 60000 में बदलें
                        if alpha_val <= 1.0:
                            alpha = int(alpha_val * 100000)
                        else:
                            alpha = int(alpha_val * 1000)
                    except ValueError:
                        pass
                
                # सुनिश्चित करें कि Alpha 100000 से ज्यादा न हो
                alpha = min(max(alpha, 0), 100000)

                # 3. धुंधलापन (Blur): 
                # अगर CSS में तीसरा मान है तो वो लें, वरना दूरी का 15% हिस्सा ब्लर रखें
                if len(parts) > 2:
                    blur = UnitConverter.to_emus(parts[2])
                else:
                    blur = int(dist * 0.15) 

                if getattr(AppConfig, 'DEBUG_TEXT_LAYOUT', False):
                     logger.debug(f"   🔍 [TextHandler] Reflection Parsed: Dist={dist}, Alpha={alpha}")


                # फाइनल डिक्शनरी (Reflection_dict) जो RunManager को जाएगी
                attributes_dict['reflection_dict'] = {
                    'dist': dist,
                    'blur': blur,
                    'alpha': alpha  # यह 'stA' टैग के लिए इस्तेमाल होगा
                }
                

            return

        # 11. TEXT GRADIENT (Enhanced with Directions)
        if prop == 'text-gradient':
            parts = val.split()
            
            # 1. Default Angle: Top-to-Bottom (5,400,000 units = 90 deg)
            angle = 5400000 
            
            # 2. Angle Logic Mapping
            if 'to-bottom' in parts: angle = 5400000    # 90 deg
            elif 'to-top' in parts:   angle = 16200000   # 270 deg
            elif 'to-right' in parts: angle = 10800000   # 180 deg
            elif 'to-left' in parts:  angle = 0          # 0 deg
            elif any('deg' in p for p in parts):
                # 45deg जैसे मैन्युअल एंगल के लिए (Basic regex math)
                try:
                    deg_val = int(''.join(filter(str.isdigit, val)))
                    angle = deg_val * 60000
                except: pass

            # 3. Colors Extraction
            exclude = ['linear', 'to-bottom', 'to-top', 'to-right', 'to-left', 'to', '45deg'] # ...etc
            colors = [p for p in parts if p not in exclude and len(p) > 2]
            
            if len(colors) >= 2:
                hex_colors = [ColorManager.get_hex(c) for c in colors]
                attributes_dict['gradient_dict'] = {
                    'colors': hex_colors,
                    'angle': angle  # 👈 अब यह डायनामिक है
                }
                attributes_dict['color'] = None 
            return

        # 12. FONT STRETCH (e.g., font-stretch: 150%)
        if prop == 'font-stretch':
            # अंक निकालें (जैसे '150%' से 150)
            import re
            nums = re.findall(r'\d+', str(value))
            if nums:
                # Word में 100 = सामान्य, 150 = 50% चौड़ा, 50 = 50% संकरा
                attributes_dict['font_stretch'] = int(nums[0])
            return

        # 13. TEXT POSITION (e.g., vertical-align: 4px)
        if prop == 'vertical-align':
            val_str = str(value).lower()
            # यदि ये कीवर्ड्स हैं तो ये sub/sup द्वारा संभाले जाएंगे (docx डिफ़ॉल्ट)
            if val_str in ['sub', 'super', 'baseline']:
                attributes_dict['vertical_align_type'] = val_str
                
                        # ✅ सुधार: Case B: Table Cell कीवर्ड्स (इन्हें सीधे सुरक्षित रखें)
            elif val_str in ['top', 'middle', 'bottom', 'center']:
                attributes_dict['vertical-align'] = val_str  # इसे dictionary में जोड़ें    
                
            else:
                # अगर नंबर है (जैसे 4px या 2pt), तो इसे हाफ-पॉइंट्स में बदलें
                import re
                num_match = re.search(r'(-?\d+\.?\d*)', val_str)
                if num_match:
                    from kritidocx.basics.unit_converter import UnitConverter
                    # पहले इसे पॉइंट्स (Pt) में बदलें, फिर 2 से गुणा करें (Half-points)
                    # मान लें UnitConverter.to_half_points उपलब्ध है
                    hps = UnitConverter.to_half_points(val_str)
                    attributes_dict['text_position'] = int(hps)
            return

        # 14. ADVANCED TEXT SHADING (e.g., background-shading: pct25 red yellow)
        if prop == 'background-shading':
            parts = val.split()
            pattern = 'solid' # डिफ़ॉल्ट
            color = 'auto'
            fill = 'transparent'

            if len(parts) >= 1:
                pattern = parts[0] # जैसे: solid, pct12, horzStripe
            if len(parts) >= 2:
                color = ColorManager.get_hex(parts[1]) # डॉट्स/लाइन का रंग
            if len(parts) >= 3:
                fill = ColorManager.get_hex(parts[2])  # बैकग्राउंड का रंग

            attributes_dict['shading_dict'] = {
                'val': pattern,
                'color': color,
                'fill': fill
            }
            return


        # Passthrough for line-height etc.
        attributes_dict[prop] = value

    @staticmethod
    def _parse_decoration(value_str, attr_dict):
        """
        Separates logic: 'underline wavy red' -> 
        {underline: True, underline_style: 'wave', underline_color: 'FF0000'}
        """
        parts = value_str.split()
        
        # Default flags
        style = 'single'
        color = None
        has_underline = 'underline' in parts
        has_strike = 'line-through' in parts or 'strike' in value_str
        
        if has_strike:
            attr_dict['strike'] = True

        if has_underline:
            attr_dict['underline'] = True
            
            # Detect Style Keywords (wavy, double, dotted)
            for part in parts:
                if part in TextHandler.DECORATION_MAP:
                    style = TextHandler.DECORATION_MAP[part]
                elif part in TextHandler.UNDERLINE_STYLES:
                    style = part
            
            attr_dict['underline_style'] = style

            # Detect Color (Hex or Name)
            # 'underline' शब्द, स्टाइल कीवर्ड्स और 'none' को छोड़कर जो बचा वो कलर हो सकता है।
            ignore_list = ['underline', 'none', 'line-through'] + \
                          list(TextHandler.DECORATION_MAP.keys()) + \
                          list(TextHandler.UNDERLINE_STYLES)
            
            for part in parts:
                if part not in ignore_list:
                    possible_hex = ColorManager.get_hex(part)
                    if possible_hex and possible_hex != '000000':
                        color = possible_hex
                        break
            
            if color:
                attr_dict['underline_color'] = color

    @staticmethod
    def _clean_font_family(raw_str):
        """
        Extracts primary font: " 'Calibri', Arial " -> "Calibri"
        """
        # Split by comma
        primary = raw_str.split(',')[0].strip()
        # Remove surrounding quotes (' or ")
        clean = primary.strip("'").strip('"')
        return clean
    
    @staticmethod
    def _expand_font_shorthand(font_str, attr_dict):
        """
        Parses CSS shorthand: [style/weight] <size>[/<line-height>] <family>
        Inputs like: 
          - "bold 14px Arial"
          - "italic small-caps bold 1rem/1.2 'Times New Roman', serif"
        """
        import re
        val = font_str.strip()
        
        # 1. Regex to find the SIZE part (The Pivot)
        # Looks for digits followed by unit OR single digits, optionally followed by /line-height
        # Capture Groups: (Pre-Size keywords) (Size) (Line-Height) (Font-Family)
        
        # Pattern Explanation:
        # ^(.*?)\s+          -> Group 1: Pre-keywords (Non-greedy start)
        # (\d+(?:\.\d+)?(?:px|pt|em|rem|%|pc|cm|in)?) -> Group 2: Font Size (Number + Unit)
        # (?:\/(\d+(?:\.\d+)?(?:px|pt|em|rem|%)?))?   -> Group 3: Optional Line Height (/20px or /1.5)
        # \s+(.*)$           -> Group 4: Font Family (Rest of string)
        
        # Note: If no units provided (like 'font: 12 Arial'), parsing is tricky, but '12' usually means px in quirks mode
        pattern = r'^(.*?)\s*(\d+(?:\.\d+)?(?:px|pt|em|rem|%|pc|cm|in)?)(?:\/(\d+(?:\.\d+)?(?:px|pt|em|rem|%)?))?\s+(.*)$'
        
        match = re.search(pattern, val)
        
        if match:
            pre_keywords = match.group(1).lower().split()
            font_size = match.group(2)
            line_height = match.group(3)
            font_family = match.group(4)
            
            # --- A. Apply Properties ---
            if font_size:
                attr_dict['font-size'] = font_size
            
            if line_height:
                attr_dict['line-height'] = line_height
                
            if font_family:
                # Reuse existing clean-up logic
                attr_dict['font-family'] = TextHandler._clean_font_family(font_family)
                
            # --- B. Process Keywords (Bold, Italic, Caps) ---
            for kw in pre_keywords:
                if kw == 'bold' or kw == 'bolder' or kw == '700':
                    attr_dict['font-weight'] = 'bold'
                    attr_dict['bold'] = True
                elif kw == 'italic' or kw == 'oblique':
                    attr_dict['font-style'] = 'italic'
                    attr_dict['italic'] = True
                elif kw == 'small-caps':
                    attr_dict['small_caps'] = True
                    # attr_dict['caps'] = True (for uppercase) is distinct from small-caps
        else:
            # Regex failed (Maybe keyword only "caption", "menu")?
            # Ignore or try basic splitting logic if crucial
            pass