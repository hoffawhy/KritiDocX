"""
from kritidocx.utils.logger import logger
POSITIONING ENGINE (The Layout Mathematician)
---------------------------------------------
Responsibility:
Calculates exact dimensions and coordinates for Media Objects.
Maps CSS Logic (Float, Absolute, Percent) to Word XML Logic (Anchor, Inline, EMUs).

Units Used:
- EMU (English Metric Unit): 1 Inch = 914,400 EMUs.
- Angles: 60,000 units = 1 Degree.

Key Features:
1. Aspect Ratio Lock (If width supplied but height missing).
2. Smart Percentage Parsing (Calculates relative to usable A4 Page width).
3. Float & Absolute logic Mapping.
4. Rotation calculation.
"""

from kritidocx.config.settings import AppConfig
from kritidocx.basics.unit_converter import UnitConverter
from kritidocx.config.constants import DocConstants
from kritidocx.config.theme import ThemeConfig
from kritidocx.utils import logger

class PositioningEngine:
    """
    Stateless Logic Class for calculating Media Layout.
    """

    # Usable Width of a Standard A4 Page (approx 6.5 inches in EMUs)
    # Used for calculating percentage widths (e.g. width="50%")
    # Logic: 8.27in - (1in left + 1in right margins) ≈ 6.27in
    USABLE_PAGE_WIDTH_EMU = int(6.27 * DocConstants.EMU_PER_INCH)

    @classmethod
    def calculate_width_emu(cls, style_data, native_px_width):
        """
        Determines the target width in EMUs.
        Priority: CSS Width (%) > CSS Width (Fixed) > HTML Attr > Native Size.
        """
        if style_data is None: style_data = {}

        
        # 1. Check CSS Percentage (width: 50%)
        # Parser puts raw strings in style_data
        w_val = style_data.get('width', '')
        
        # Explicit Percentage Handling
        if isinstance(w_val, str) and '%' in w_val:
            try:
                percent = float(w_val.replace('%', ''))
                return int(cls.USABLE_PAGE_WIDTH_EMU * (percent / 100.0))
            except ValueError:
                pass # Fallback

        # 2. Check CSS Fixed Value (px, cm, in, pt)
        width_emu = UnitConverter.to_emus(w_val)
        if width_emu > 0:
            return width_emu

        # 3. Fallback: Native Image Size (Pixels)
        # Convert logic: Native Px -> EMUs (assuming 96 DPI default)
        return int(native_px_width * DocConstants.EMU_PER_PIXEL)

    @classmethod
    def calculate_height_emu(cls, style_data, native_px_height, current_width_emu, native_px_width):
        """
        Determines target height.
        Logic: Maintains Aspect Ratio if Height is 'auto' or missing.
        """
        h_val = style_data.get('height', '')
        
        # 1. Check Fixed CSS Value
        # Note: Vertical percentage is unreliable in Word contexts, usually implies fixed or aspect.
        height_emu = UnitConverter.to_emus(h_val)
        
        if height_emu > 0:
            return height_emu

        # 2. Aspect Ratio Math
        # New Height = (New Width * Old Height) / Old Width
        if native_px_width > 0:
            ratio = native_px_height / native_px_width
            return int(current_width_emu * ratio)
        
        # Fallback (Should typically not reach here unless 0-width image)
        return current_width_emu

    @classmethod
    def resolve_positioning(cls, style_data):
        """
        Decides Layout Mode based on CSS.
        """
        if style_data is None: style_data = {}
        
        # [UPDATED DICTIONARY STRUCTURE]
        config = {
            'is_floating': False,
            # Wrap Distances (Padding between text and box)
            'distT': 0, 'distB': 0, 'distL': 0, 'distR': 0,
            # Alignments
            'align_h': None,        
            'pos_x': 0, 'pos_y': 0, 
            'rel_h': 'column',      
            'rel_v': 'paragraph',
            'origin': 'column',     # New key for explicit origin
            # Behaviors
            'wrap_type': 'none',    # Default to Overlay if floating
            'z_index': 0,
            'rotation': 0,
            'behind_doc': False,
            'locked': False
        }

        # 1. TEXT WRAP DISTANCE (Mapping CSS Margins to Word 'Distances')
        # Word needs EMUs. Usually css margin on floating element = distance from text.
        # We cap it at ~0.5 inch (457200) to prevent layout breakage.
        def _get_dist(key):
            val = style_data.get(f'margin-{key}') or style_data.get(key)
            if val:
                # 'auto' margins handled elsewhere, here strictly numeric distance
                if val == 'auto': return 0
                return min(UnitConverter.to_emus(str(val)), 457200) 
            return 0 # Default Word uses 0 or ~114300 (0.125")

        config['distT'] = _get_dist('top')
        config['distB'] = _get_dist('bottom')
        config['distL'] = _get_dist('left')
        config['distR'] = _get_dist('right')



        # -----------------------------------------------
        # 2. ROTATION & TRANSFORMS
        # -----------------------------------------------
        # Math: 1 Degree = 60,000 units
        rot_deg = style_data.get('rotation_deg')
        
        if rot_deg is not None:
            try:
                # Rotation exists -> Must Force Floating
                config['rotation'] = int(float(rot_deg) * 60000)
                config['is_floating'] = True
                
                # रोटेटेड ऑब्जेक्ट्स के लिए 'None' (Overlay) सबसे सुरक्षित रैप टाइप है
                config['wrap_type'] = 'none' 
            except ValueError:
                pass

        # -----------------------------------------------
        # 3. Z-INDEX (Layers)
        # -----------------------------------------------
        raw_z = style_data.get('z-index') or style_data.get('z_index')
        if raw_z and str(raw_z).lower() != 'auto':
            try:
                z = int(raw_z)
                config['z_index'] = z
                # Negative Z-Index = Behind Text
                if z < 0: config['behind_doc'] = True
                # Z-index usually implies non-standard flow
                if z != 0: config['is_floating'] = True
            except: pass

        # -----------------------------------------------
        # 4. POSITION MODE: ABSOLUTE / FIXED
        # -----------------------------------------------
        pos_mode = str(style_data.get('position', '')).lower()
        
        if pos_mode in ['absolute', 'fixed']:
            config['is_floating'] = True
            
            # --- [SMART WRAP CONTROL]: [UPDATE] ---
            # डिफ़ॉल्ट रूप से Overlay (none) रखें ताकि 'Stamps' या 'Badges' के काम आ सके (आपका तर्क)
            # लेकिन अगर HTML में विशेष रूप से 'wrap' माँगा गया है, तो उसे अनुमति दें।
            user_wrap = style_data.get('wrap') or style_data.get('data-wrap')
            if user_wrap == 'square' or user_wrap == 'tight':
                config['wrap_type'] = user_wrap
            else:
                config['wrap_type'] = 'none' # Standard Absolute Overlay (True to CSS)
            
            l_val = style_data.get('left')
            r_val = style_data.get('right')
            t_val = style_data.get('top')
            b_val = style_data.get('bottom')
            
            # --- [SMART ORIGIN DETECTION] ---
            # 1. HTML Override: क्या यूज़र ने खुद बताया है?
            user_origin = style_data.get('origin', '').lower().strip()
            
            # 2. Config Defaults & Consistency Logic
            # [ALIGNMENT SYMMETRY FIX]
            # समस्या: Left/Top 'Page' (0,0) से शुरू हो रहे थे, लेकिन Right 'Margin' पर रुक रहा था।
            # समाधान: Absolute बॉक्स के लिए Right/Bottom को भी डिफ़ॉल्ट रूप से 'Page Edge' (Page) मानें।
            # अगर यूज़र को मार्जिन चाहिए, तो वे 'origin: margin' HTML में लिख सकते हैं।
            
            def_coord = 'page' 
            def_align = 'page' # पहले यह 'margin' था, अब इसे 'page' कर दिया गया है।
            
            # (वैकल्पिक: आप ThemeConfig से भी इसे कंट्रोल कर सकते हैं, पर यहाँ हार्डकोड करना सुरक्षित है
            # ताकि यह web-like व्यवहार की गारंटी दे सके)
  
            # 3. Base Selection Logic
            h_base_custom = None
            v_base_custom = None

            if user_origin:
                # यदि यूज़र ने explicit कहा है (Paragraph/Margin/Page)
                map_org = {
                    'paragraph': 'column', # Word uses 'column' for horz align relative to text
                    'text': 'column',
                    'margin': 'margin',
                    'page': 'page'
                }
                h_base_custom = map_org.get(user_origin, 'page') # Fallback to page if typo
                v_base_custom = 'paragraph' if user_origin in ['paragraph', 'text'] else h_base_custom

            
            # --- HORIZONTAL AXIS ---
            if l_val and l_val != 'auto':
                config['pos_x'] = UnitConverter.to_emus(str(l_val))
                config['rel_h'] = h_base_custom if h_base_custom else def_coord
                
                if getattr(AppConfig, 'DEBUG_POSITIONING', False): 
                    logger.debug(f"      👉 X: {config['pos_x']} (Left)")

            elif r_val and r_val != 'auto':
                # [OFFSET FIX]: Check if it is exactly 0
                val_emu = UnitConverter.to_emus(str(r_val))
                
                if val_emu == 0:
                    # CASE A: Stick to Edge (align="right")
                    config['align_h'] = 'right'
                    config['rel_h'] = h_base_custom if h_base_custom else def_align
                else:
                    # CASE B: Offset from Edge (Calculate manually)
                    # HTML Right implies moving LEFT from the edge.
                    # Word supports relativeFrom="rightMargin".
                    # We utilize "rightMargin" and Negative Offset (-X) to push 'IN' towards page center.
                    config['align_h'] = None
                    config['pos_x'] = -val_emu  # Negative moves leftwards
                    config['rel_h'] = 'rightMargin' 
                
                if getattr(AppConfig, 'DEBUG_POSITIONING', False): 
                    logger.debug(f"      👉 Right Action: {'Align' if config.get('align_h') else 'Offset'} | Val: {r_val}")

            # --- VERTICAL AXIS ---
            if t_val and t_val != 'auto':
                config['pos_y'] = UnitConverter.to_emus(str(t_val))
                config['rel_v'] = v_base_custom if v_base_custom else def_coord
                
                if getattr(AppConfig, 'DEBUG_POSITIONING', False): 
                    logger.debug(f"      👉 Y: {config['pos_y']} (Top)")

            elif b_val and b_val != 'auto':
                # [OFFSET FIX]: Bottom Logic
                val_emu = UnitConverter.to_emus(str(b_val))
                
                if val_emu == 0:
                    # CASE A: Stick to Bottom (align="bottom")
                    config['align_v'] = 'bottom'
                    config['rel_v'] = v_base_custom if v_base_custom else def_align
                else:
                    # CASE B: Offset from Bottom (Move Up)
                    # relativeFrom="bottomMargin", Negative Offset moves UP.
                    config['align_v'] = None
                    config['pos_y'] = -val_emu
                    config['rel_v'] = 'bottomMargin'
                
                if getattr(AppConfig, 'DEBUG_POSITIONING', False): 
                    logger.debug(f"      👉 Bottom Action: {'Align' if config.get('align_v') else 'Offset'} | Val: {b_val}")
                    
            return config


        # -----------------------------------------------
        # 5. FLOAT MODE (Legacy Wrapping)
        # -----------------------------------------------
        # [CRITICAL FIX]: Secure Context-Lock for Wrapping Flow
        f_raw = style_data.get('float')
        float_val = str(f_raw).lower() if f_raw else ''
        
        a_raw = style_data.get('align')
        align_attr = str(a_raw).lower() if a_raw else '' 

        target_align = None
        if float_val in ['left', 'right']: target_align = float_val
        elif align_attr in ['left', 'right']: target_align = align_attr

        if target_align:
            config['is_floating'] = True
            config['wrap_type'] = 'square' # Wrapping Active
            config['align_h'] = target_align 
            
            # [CRITICAL UPDATE]: Apply Margins as Physical Offsets
            # यदि मार्जिन नेगेटिव है (जैसे -150px), तो बॉक्स को ऊपर शिफ्ट करें।
            m_top = style_data.get('margin-top') or style_data.get('margin_top')
            if m_top:
                # margin-top को Y-offset में बदलें (Word coordinate math)
                config['pos_y'] = UnitConverter.to_emus(str(m_top))
                # यदि हमने ऑफसेट दिया है, तो 'top' एलाइनमेंट के सापेक्ष उसे रखें
                config['align_v'] = None 
                config['rel_v'] = 'paragraph' 
            else:
                config['rel_v'] = 'line'
                config['align_v'] = 'top'

            config['rel_h'] = 'column'
            config['allow_overlap'] = False 

            if getattr(AppConfig, 'DEBUG_POSITIONING', False):
                logger.debug(f"      ⚓ Float Offset: {config.get('pos_y')} EMUs")


        return config